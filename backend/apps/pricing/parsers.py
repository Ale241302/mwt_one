# Sprint 22 - S22-11: Parser de pricelist Marluvas (CSV y Excel)
# Columnas esperadas: Referência, Preço, Grade,
#   33/34, 35/36, 37/38, 39/40, 41/42, 43/44, 45/46, 47/48,
#   Cabedal, Bico, Palmilha, NCM, CA, Código, Centro
import uuid
import io

# Cache en memoria de sesiones de upload (sustituye Redis en MVP)
# { session_id: { 'valid_rows': [...], 'warnings': [...], 'errors': [...], 'brand_id': int } }
_UPLOAD_SESSIONS = {}

# Columnas de tallas reconocidas
SIZE_COLUMNS = [
    '33/34', '35/36', '37/38', '39/40',
    '41/42', '43/44', '45/46', '47/48',
]

# Mapa de aliases de columnas (tolera mayúsculas, acentos, variantes)
COLUMN_ALIASES = {
    # Referencia
    'referência': 'reference_code',
    'referencia': 'reference_code',
    'ref': 'reference_code',
    'referência ': 'reference_code',
    # Precio
    'preço': 'unit_price_usd',
    'preco': 'unit_price_usd',
    'preço (usd)': 'unit_price_usd',
    'preco (usd)': 'unit_price_usd',
    'price': 'unit_price_usd',
    # Grade
    'grade': 'grade_label',
    # Metadata
    'cabedal': 'tip_type',
    'bico': 'insole_type',
    'palmilha': 'insole_type',  # fallback si no hay Bico
    'ncm': 'ncm',
    'ca': 'ca_number',
    'código': 'factory_code',
    'codigo': 'factory_code',
    'centro': 'factory_center',
}


def _normalize_col(col):
    """Normaliza nombre de columna: strip + lower + sin espacios dobles."""
    return str(col).strip().lower().replace('\xa0', ' ')


def _read_file(file):
    """
    Lee el archivo y retorna un DataFrame de pandas.
    Soporta .csv y .xlsx / .xls.
    Lanza ValueError si el formato no es reconocido.
    """
    try:
        import pandas as pd
    except ImportError:
        raise ImportError('pandas no está instalado. Agrega pandas y openpyxl a requirements.')

    name = getattr(file, 'name', '') or ''
    extension = name.lower().split('.')[-1] if '.' in name else ''

    raw = file.read()
    if not raw:
        raise ValueError('El archivo está vacío.')

    if extension in ('xlsx', 'xls'):
        try:
            df = pd.read_excel(io.BytesIO(raw), dtype=str, engine='openpyxl')
        except Exception:
            # Fallback a motor por defecto si openpyxl falla
            df = pd.read_excel(io.BytesIO(raw), dtype=str)
    elif extension == 'csv':
        # Intenta UTF-8 primero, luego latin-1
        try:
            df = pd.read_csv(io.BytesIO(raw), dtype=str, encoding='utf-8')
        except UnicodeDecodeError:
            df = pd.read_csv(io.BytesIO(raw), dtype=str, encoding='latin-1')
    else:
        # Si no hay extensión clara, intenta CSV
        try:
            df = pd.read_csv(io.BytesIO(raw), dtype=str, encoding='utf-8')
        except Exception:
            raise ValueError(
                f'Formato de archivo no reconocido: "{name}". '
                'Sube un archivo .csv o .xlsx'
            )

    # Strip nombres de columna
    df.columns = [str(c).strip() for c in df.columns]
    return df


def _map_columns(df):
    """
    Renombra columnas del DataFrame usando COLUMN_ALIASES.
    Columnas de tallas se detectan automáticamente.
    Retorna (df_renamed, detected_size_cols, missing_required)
    """
    rename_map = {}
    detected_size_cols = []

    used_aliases = set()
    for col in df.columns:
        norm = _normalize_col(col)
        if norm in COLUMN_ALIASES:
            alias = COLUMN_ALIASES[norm]
            if alias not in used_aliases:
                rename_map[col] = alias
                used_aliases.add(alias)
        elif norm in [s.lower() for s in SIZE_COLUMNS]:
            # Normaliza talla a formato estándar (ej. '33/34')
            detected_size_cols.append(col)
        # Columnas no reconocidas se ignoran

    df = df.rename(columns=rename_map)

    # Verificar columnas requeridas (ahora deshabilitado según solicitud)
    required = []
    missing = []
    return df, detected_size_cols, missing


def parse_marluvas_pricelist(file, brand_id=None):
    """
    Parsea un archivo CSV/Excel con estructura de pricelist Marluvas.

    Retorna dict con:
    {
        session_id: str,          # usar en /confirm/
        valid_lines: int,
        warnings: list,
        errors: list,
        preview: list,            # primeras 5 líneas válidas
    }
    NO crea ningún objeto en DB.
    """
    warnings = []
    errors = []
    valid_rows = []

    # 1. Leer archivo
    try:
        df = _read_file(file)
    except (ValueError, ImportError) as e:
        return {
            'session_id': None,
            'valid_lines': 0,
            'warnings': [],
            'errors': [{'row': None, 'message': str(e)}],
            'preview': [],
        }

    if df.empty:
        return {
            'session_id': None,
            'valid_lines': 0,
            'warnings': [],
            'errors': [{'row': None, 'message': 'El archivo no contiene filas de datos.'}],
            'preview': [],
        }

    # 2. Mapear columnas
    df, size_cols, missing_required = _map_columns(df)

    if missing_required:
        return {
            'session_id': None,
            'valid_lines': 0,
            'warnings': [],
            'errors': [{
                'row': None,
                'message': (
                    f'Columnas requeridas no encontradas: {", ".join(missing_required)}. '
                    f'Columnas presentes: {", ".join(df.columns.tolist())}'
                ),
            }],
            'preview': [],
        }

    if not size_cols:
        warnings.append({
            'row': None,
            'message': (
                'No se detectaron columnas de tallas (ej. 33/34, 35/36...). '
                'Los size_multipliers estarán vacíos.'
            ),
        })

    # 3. Parsear fila por fila
    import pandas as pd

    for idx, row in df.iterrows():
        row_num = idx + 2  # +2 porque idx 0-based y fila 1 = header

        reference_code = str(row.get('reference_code', '') or '').strip()
        if not reference_code or reference_code.lower() in ('nan', 'none', ''):
            warnings.append({
                'row': row_num,
                'message': f'Fila {row_num}: reference_code vacío — fila ignorada.',
            })
            continue

        # Precio
        raw_price = str(row.get('unit_price_usd', '') or '').strip().replace(',', '.')
        try:
            unit_price_usd = float(raw_price)
            if unit_price_usd <= 0:
                raise ValueError('precio <= 0')
        except (ValueError, TypeError):
            errors.append({
                'row': row_num,
                'message': f'Fila {row_num}: precio inválido "{raw_price}" para ref {reference_code}.',
            })
            continue

        # Grade
        grade_label = str(row.get('grade_label', '') or '').strip()
        if grade_label.lower() in ('nan', 'none'):
            grade_label = ''

        # Metadata
        def _safe(col):
            v = str(row.get(col, '') or '').strip()
            return '' if v.lower() in ('nan', 'none') else v

        # size_multipliers: {talla: multiplicador}
        size_multipliers = {}
        for col in size_cols:
            raw_val = str(row.get(col, '') or '').strip()
            if raw_val and raw_val.lower() not in ('nan', 'none', '0', ''):
                try:
                    multiplier = int(float(raw_val))
                    if multiplier > 0:
                        size_multipliers[col] = multiplier
                except (ValueError, TypeError):
                    warnings.append({
                        'row': row_num,
                        'message': (
                            f'Fila {row_num}: valor de talla "{col}" = "{raw_val}" no es número — ignorado.'
                        ),
                    })

        parsed_row = {
            'reference_code': reference_code,
            'unit_price_usd': round(unit_price_usd, 4),
            'grade_label': grade_label,
            'tip_type': _safe('tip_type'),
            'insole_type': _safe('insole_type'),
            'ncm': _safe('ncm'),
            'ca_number': _safe('ca_number'),
            'factory_code': _safe('factory_code'),
            'factory_center': _safe('factory_center'),
            'size_multipliers': size_multipliers,
        }
        valid_rows.append(parsed_row)

    # 4. Guardar sesión en memoria
    session_id = str(uuid.uuid4())
    _UPLOAD_SESSIONS[session_id] = {
        'valid_rows': valid_rows,
        'warnings': warnings,
        'errors': errors,
        'brand_id': brand_id,
    }

    return {
        'session_id': session_id,
        'valid_lines': len(valid_rows),
        'warnings': warnings,
        'errors': errors,
        'preview': valid_rows[:5],
    }


def get_upload_session(session_id):
    """Recupera una sesión de upload por su ID. Retorna None si no existe."""
    return _UPLOAD_SESSIONS.get(session_id)


def clear_upload_session(session_id):
    """Elimina la sesión de la memoria tras confirmar."""
    _UPLOAD_SESSIONS.pop(session_id, None)
