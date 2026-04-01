# S20-05 / S21 — ArtifactPolicy engine
# Fuente única de verdad para modos permitidos y políticas de artefactos por brand.
# S21: Agrega soporte para custom_artifact_policy por expediente (admin overrides).
# NO duplicar BRAND_ALLOWED_MODES en ningún otro archivo; importar siempre desde aquí.
#
# FIX-2026-03-31:
#   - brand es ForeignKey a brands.Brand (no tiene .slug). Se usa brand.name.lower().
#   - status filter corregido de 'COMPLETED' a 'completed' (lowercase según ArtifactStatusEnum).

from __future__ import annotations

# ---------------------------------------------------------------------------
# 1. Modos permitidos por brand
# ---------------------------------------------------------------------------
BRAND_ALLOWED_MODES: dict[str, tuple[str, ...]] = {
    'marluvas':  ('mode_b', 'mode_c'),
    'rana_walk': ('default',),
    'tecmater':  ('default',),
}

# ---------------------------------------------------------------------------
# 2. Política canónica base por estado del expediente (independiente de brand).
#
#    Usada como policy base en "Modo Libre / Admin":
#      — Todos los artefactos listados son OPCIONALES para el admin
#      — El admin puede agregar o quitar via custom_artifact_policy
#
#    Artículos con etiquetas canónicas (definición en ARTIFACT_LABELS):
#      ART-01  Orden de Compra (OC)
#      ART-02  Proforma / Confirmed Invoice
#      ART-03  Decisión Modal
#      ART-04  SAP Confirmado
#      ART-05  Embarque Registrado
#      ART-06  Confirmación Producción
#      ART-07  Despacho Aprobado
#      ART-08  Cotización Flete
#      ART-09  Factura Aduanal (Customs)
#      ART-10  BL Registrado (Bill of Lading)
#      ART-11  Nota de Entrega
#      ART-12  Nota de Compensación
#      ART-13  Factura MWT
#      ART-16  Motivo Cancelación
#      ART-19  Decisión Logística
#      ART-36  Actualización Tracking
# ---------------------------------------------------------------------------

# Política CANÓNICA base — define qué artefactos son relevantes para cada estado.
# El resolve_artifact_policy los tratará todos como opcionales (Modo Libre).
CANONICAL_STATE_ARTIFACTS: dict[str, list[str]] = {
    'REGISTRO':     ['ART-01', 'ART-02'],
    'PRODUCCION':   ['ART-04', 'ART-06'],
    'PREPARACION':  ['ART-03', 'ART-05', 'ART-08'],
    'DESPACHO':     ['ART-07', 'ART-09', 'ART-12'],
    'TRANSITO':     ['ART-10', 'ART-36'],
    'EN_DESTINO':   ['ART-13', 'ART-11'],
    'CERRADO':      [],
    'CANCELADO':    ['ART-16'],
}

# Etiquetas humanas para la UI
ARTIFACT_LABELS: dict[str, str] = {
    'ART-01':  'Orden de Compra',
    'ART-02':  'Proforma',
    'ART-03':  'Decisión Modal',
    'ART-04':  'SAP Confirmado',
    'ART-05':  'Embarque',
    'ART-06':  'Confirmación Producción',
    'ART-07':  'Despacho Aprobado',
    'ART-08':  'Cotización Flete',
    'ART-09':  'Despacho Aduanal',
    'ART-10':  'BL Registrado',
    'ART-11':  'Nota de Entrega',
    'ART-12':  'Nota de Compensación',
    'ART-13':  'Factura MWT',
    'ART-16':  'Motivo Cancelación',
    'ART-19':  'Decisión Logística',
    'ART-36':  'Actualización Tracking',
}

# Todos los artefactos conocidos — usados para validar tipos al agregar
ALL_KNOWN_ARTIFACTS: list[str] = sorted(ARTIFACT_LABELS.keys())

# ---------------------------------------------------------------------------
# 3. Tabla de políticas por brand → mode → estado → {required, optional, gate_for_advance}
#    Usada cuando el expediente tiene proformas (proforma-driven mode).
# ---------------------------------------------------------------------------
ARTIFACT_POLICY: dict[str, dict[str, dict[str, dict[str, list[str]]]]] = {
    'marluvas': {
        'mode_b': {
            'REGISTRO': {
                'required':         ['ART-01'],
                'optional':         ['ART-02'],
                'gate_for_advance': ['ART-01'],
            },
            'PREPARACION': {
                'required':         ['ART-02', 'ART-03', 'ART-04'],
                'optional':         ['ART-09'],
                'gate_for_advance': ['ART-02', 'ART-03', 'ART-04'],
            },
            'PRODUCCION': {
                'required':         ['ART-04', 'ART-06'],
                'optional':         ['ART-08'],
                'gate_for_advance': ['ART-04', 'ART-06'],
            },
            'DESPACHO': {
                'required':         ['ART-05', 'ART-07', 'ART-09'],
                'optional':         ['ART-10', 'ART-12'],
                'gate_for_advance': ['ART-05', 'ART-07', 'ART-09'],
            },
            'TRANSITO': {
                'required':         ['ART-10'],
                'optional':         ['ART-36'],
                'gate_for_advance': ['ART-10'],
            },
            'EN_DESTINO': {
                'required':         ['ART-13'],
                'optional':         ['ART-11'],
                'gate_for_advance': ['ART-13'],
            },
            'CERRADO':   {'required': [], 'optional': [], 'gate_for_advance': []},
            'CANCELADO': {'required': [], 'optional': ['ART-16'], 'gate_for_advance': []},
        },
        'mode_c': {
            'REGISTRO': {
                'required':         ['ART-01'],
                'optional':         ['ART-02'],
                'gate_for_advance': ['ART-01'],
            },
            'PREPARACION': {
                'required':         ['ART-02', 'ART-03'],
                'optional':         ['ART-04', 'ART-09'],
                'gate_for_advance': ['ART-02', 'ART-03'],
            },
            'PRODUCCION': {
                'required':         ['ART-06'],
                'optional':         ['ART-04', 'ART-08'],
                'gate_for_advance': ['ART-06'],
            },
            'DESPACHO': {
                'required':         ['ART-05', 'ART-09'],
                'optional':         ['ART-07', 'ART-10', 'ART-12'],
                'gate_for_advance': ['ART-05', 'ART-09'],
            },
            'TRANSITO': {
                'required':         ['ART-10'],
                'optional':         ['ART-36'],
                'gate_for_advance': ['ART-10'],
            },
            'EN_DESTINO': {
                'required':         ['ART-13'],
                'optional':         ['ART-11'],
                'gate_for_advance': ['ART-13'],
            },
            'CERRADO':   {'required': [], 'optional': [], 'gate_for_advance': []},
            'CANCELADO': {'required': [], 'optional': ['ART-16'], 'gate_for_advance': []},
        },
    },
    'rana_walk': {
        'default': {
            'REGISTRO': {
                'required':         ['ART-01'],
                'optional':         ['ART-02'],
                'gate_for_advance': ['ART-01'],
            },
            'PREPARACION': {
                'required':         ['ART-02'],
                'optional':         ['ART-08'],
                'gate_for_advance': ['ART-02'],
            },
            'PRODUCCION': {
                'required':         [],
                'optional':         ['ART-06'],
                'gate_for_advance': [],
            },
            'DESPACHO': {
                'required':         ['ART-05', 'ART-09'],
                'optional':         ['ART-07', 'ART-10', 'ART-12'],
                'gate_for_advance': ['ART-05', 'ART-09'],
            },
            'TRANSITO': {
                'required':         ['ART-10'],
                'optional':         ['ART-36'],
                'gate_for_advance': ['ART-10'],
            },
            'EN_DESTINO': {
                'required':         ['ART-13'],
                'optional':         ['ART-11'],
                'gate_for_advance': ['ART-13'],
            },
            'CERRADO':   {'required': [], 'optional': [], 'gate_for_advance': []},
            'CANCELADO': {'required': [], 'optional': ['ART-16'], 'gate_for_advance': []},
        },
    },
    'tecmater': {
        'default': {
            'REGISTRO': {
                'required':         ['ART-01'],
                'optional':         ['ART-02'],
                'gate_for_advance': ['ART-01'],
            },
            'PREPARACION': {
                'required':         ['ART-02', 'ART-03', 'ART-04'],
                'optional':         ['ART-08'],
                'gate_for_advance': ['ART-02', 'ART-04'],
            },
            'PRODUCCION': {
                'required':         ['ART-04', 'ART-06'],
                'optional':         ['ART-08'],
                'gate_for_advance': ['ART-04'],
            },
            'DESPACHO': {
                'required':         ['ART-05', 'ART-09'],
                'optional':         ['ART-07', 'ART-10', 'ART-12'],
                'gate_for_advance': ['ART-05', 'ART-09'],
            },
            'TRANSITO': {
                'required':         ['ART-10'],
                'optional':         ['ART-36'],
                'gate_for_advance': ['ART-10'],
            },
            'EN_DESTINO': {
                'required':         ['ART-13'],
                'optional':         ['ART-11'],
                'gate_for_advance': ['ART-13'],
            },
            'CERRADO':   {'required': [], 'optional': [], 'gate_for_advance': []},
            'CANCELADO': {'required': [], 'optional': ['ART-16'], 'gate_for_advance': []},
        },
    },
}

# ---------------------------------------------------------------------------
# 4. Fallback genérico: usa CANONICAL_STATE_ARTIFACTS para todos los estados
# ---------------------------------------------------------------------------
GENERIC_POLICY: dict = {
    state: {
        'required':         [],
        'optional':         list(artifacts),
        'gate_for_advance': [],
    }
    for state, artifacts in CANONICAL_STATE_ARTIFACTS.items()
}


def _get_brand_slug(expediente) -> str:
    """
    FIX-2026-03-31: brand es ForeignKey a brands.Brand.
    Brand NO tiene .slug — se normaliza brand.name a lowercase con guion bajo.
    Ejemplos: 'Marluvas' -> 'marluvas', 'Rana Walk' -> 'rana_walk'.
    Si el brand no existe o falla, retorna string vacío.
    """
    try:
        brand_obj = expediente.brand
        if brand_obj is None:
            return ''
        # Intenta .slug si existe (por si se agrega en el futuro)
        if hasattr(brand_obj, 'slug') and brand_obj.slug:
            return brand_obj.slug.lower()
        # Normalización desde .name
        name = getattr(brand_obj, 'name', '') or ''
        return name.lower().replace(' ', '_').replace('-', '_')
    except Exception:
        return ''


def _apply_custom_policy(base_policy: dict, custom: dict) -> dict:
    """
    S21: Aplica las custom_artifact_policy del expediente sobre la política base.

    custom tiene estructura:
      { "ESTADO": { "add": ["ART-XX"], "remove": ["ART-YY"] } }

    Reglas:
    - add: agrega artefactos a la lista opcional del estado (dedup)
    - remove: elimina artefactos de required y optional del estado
    - Se crea el estado en la policy si no existe aún (para estados futuros)
    """
    result = {}
    # Copia base
    for state, rules in base_policy.items():
        result[state] = {
            'required':         list(rules.get('required', [])),
            'optional':         list(rules.get('optional', [])),
            'gate_for_advance': list(rules.get('gate_for_advance', [])),
        }

    # Aplica overrides
    for state, ops in custom.items():
        if state not in result:
            result[state] = {'required': [], 'optional': [], 'gate_for_advance': []}

        to_add = ops.get('add', [])
        to_remove = set(ops.get('remove', []))

        # Agrega a optional (si no está ya en required)
        for art in to_add:
            if art not in result[state]['required'] and art not in result[state]['optional']:
                result[state]['optional'].append(art)

        # Elimina de required, optional y gate, pero solo si no está en to_add
        final_remove = [a for a in to_remove if a not in to_add]
        
        result[state]['required']         = [a for a in result[state]['required']         if a not in final_remove]
        result[state]['optional']         = [a for a in result[state]['optional']         if a not in final_remove]
        result[state]['gate_for_advance'] = [a for a in result[state]['gate_for_advance'] if a not in final_remove]

    return result


# ---------------------------------------------------------------------------
# 5. resolve_artifact_policy(expediente) → dict JSON-serializable
# ---------------------------------------------------------------------------
def resolve_artifact_policy(expediente) -> dict:
    """
    Calcula dinámicamente la política de artefactos para un expediente.

    Lógica (S21 mode):
    1. Si sin proformas → usa CANONICAL_STATE_ARTIFACTS en Modo Libre (todo opcional)
    2. Si con proformas → merge de policies por mode (igual que antes) en Modo Libre
    3. Aplica custom_artifact_policy del expediente (add / remove por estado)
    4. Output siempre JSON-serializable (listas, no sets)

    FIX-2026-03-31:
    - brand_slug se obtiene via _get_brand_slug() (brand.name.lower(), no .slug)
    - status filter usa 'completed' lowercase (ArtifactStatusEnum almacena lowercase)
    """
    from apps.expedientes.models import ArtifactInstance  # import local para evitar circular

    brand_slug: str = _get_brand_slug(expediente)
    brand_policy = ARTIFACT_POLICY.get(brand_slug, {})

    # FIX: ArtifactStatusEnum almacena 'completed' en lowercase, NO 'COMPLETED'
    proformas = list(
        ArtifactInstance.objects.filter(
            expediente=expediente,
            artifact_type='ART-02',
            status='completed',
        ).values('payload')
    )

    # --- Política base (antes del merge con proformas) ---
    if not proformas:
        # Sin proformas → usa política canónica en Modo Libre
        if brand_policy:
            mode = 'default' if 'default' in brand_policy else next(iter(brand_policy))
            raw_policy = brand_policy[mode]
            base: dict = _as_libre(raw_policy)
        else:
            base = dict(GENERIC_POLICY)
    else:
        # Brand desconocida con proformas → fallback canónico
        if not brand_policy:
            base = dict(GENERIC_POLICY)
        else:
            # Merge de policies por cada proforma
            merged: dict[str, dict[str, set]] = {}
            for pf in proformas:
                payload = pf.get('payload') or {}
                mode = payload.get('mode', 'default')
                pf_policy = brand_policy.get(mode, {})
                if not pf_policy:
                    continue
                for state, rules in pf_policy.items():
                    if state not in merged:
                        merged[state] = {
                            'required':         set(),
                            'optional':         set(),
                            'gate_for_advance': set(),
                        }
                    merged[state]['required']         |= set(rules.get('required', []))
                    merged[state]['optional']         |= set(rules.get('optional', []))
                    merged[state]['gate_for_advance'] |= set(rules.get('gate_for_advance', []))

            if not merged:
                base = dict(GENERIC_POLICY)
            else:
                # Normalización: Modo Libre — todo opcional
                base = _as_libre(merged)

    # --- Asegurarse que todos los estados canónicos están presentes ---
    for state in CANONICAL_STATE_ARTIFACTS:
        if state not in base:
            base[state] = {
                'required':         [],
                'optional':         list(CANONICAL_STATE_ARTIFACTS[state]),
                'gate_for_advance': [],
            }

    # --- S21: Aplicar overrides del expediente ---
    custom = getattr(expediente, 'custom_artifact_policy', None) or {}
    if custom:
        base = _apply_custom_policy(base, custom)

    # --- S21: Garantía de visibilidad para REGISTRO (Inteligente) ---
    # Solo agregamos back OC/Proforma si NO fueron removidas explícitamente por el admin.
    if 'REGISTRO' in base:
        removed_arts = set(custom.get('REGISTRO', {}).get('remove', []))
        added_arts   = set(custom.get('REGISTRO', {}).get('add', []))
        
        reg_arts = set(base['REGISTRO']['required']) | set(base['REGISTRO']['optional'])
        for core_art in ['ART-01', 'ART-02']:
            # Solo forzar si falta Y no fue removido (o si fue removido pero luego agregado)
            is_explicitly_removed = core_art in removed_arts and core_art not in added_arts
            if core_art not in reg_arts and not is_explicitly_removed:
                base['REGISTRO']['optional'].append(core_art)

    return base


def _as_libre(policy_or_merged) -> dict:
    """
    Modo Libre: Dado un dict de estados→rules (ya sean sets o listas), convierte
    todo a opcional. Soporta tanto dicts de listas (ARTIFACT_POLICY) como
    dicts de sets (merged).
    """
    result = {}
    for state, rules in policy_or_merged.items():
        if isinstance(rules, dict):
            req  = rules.get('required', [])
            opt  = rules.get('optional', [])
            gate = rules.get('gate_for_advance', [])
            all_arts = set(req) | set(opt) | set(gate)
        else:
            all_arts = set(rules)  # fallback

        result[state] = {
            'required':         [],
            'optional':         sorted(list(all_arts)),
            'gate_for_advance': [],
        }
    return result
