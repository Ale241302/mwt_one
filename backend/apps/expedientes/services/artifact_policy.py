# S20-05 — ArtifactPolicy engine
# Fuente única de verdad para modos permitidos y políticas de artefactos por brand.
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
# 2. Tabla de políticas por brand → mode → estado → {required, optional, gate_for_advance}
#
#    Artefact codes:
#      ART-01  Solicitud de pedido
#      ART-02  Proforma
#      ART-03  OC cliente
#      ART-04  OC fábrica
#      ART-05  BL / AWB
#      ART-06  Packing list
#      ART-07  Certificado de origen
#      ART-08  Certificado de calidad
#      ART-09  Factura comercial
#      ART-10  Comprobante de pago
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
                'required':         ['ART-04', 'ART-08'],
                'optional':         ['ART-06'],
                'gate_for_advance': ['ART-04', 'ART-08'],
            },
            'DESPACHO': {
                'required':         ['ART-05', 'ART-06', 'ART-07', 'ART-09'],
                'optional':         ['ART-10'],
                'gate_for_advance': ['ART-05', 'ART-06', 'ART-09'],
            },
            'TRANSITO': {
                'required':         ['ART-05', 'ART-10'],
                'optional':         [],
                'gate_for_advance': ['ART-10'],
            },
            'DESTINO': {
                'required':         ['ART-10'],
                'optional':         [],
                'gate_for_advance': ['ART-10'],
            },
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
                'required':         ['ART-08'],
                'optional':         ['ART-04', 'ART-06'],
                'gate_for_advance': ['ART-08'],
            },
            'DESPACHO': {
                'required':         ['ART-05', 'ART-06', 'ART-09'],
                'optional':         ['ART-07', 'ART-10'],
                'gate_for_advance': ['ART-05', 'ART-06', 'ART-09'],
            },
            'TRANSITO': {
                'required':         ['ART-05', 'ART-10'],
                'optional':         [],
                'gate_for_advance': ['ART-10'],
            },
            'DESTINO': {
                'required':         ['ART-10'],
                'optional':         [],
                'gate_for_advance': ['ART-10'],
            },
        },
    },
    'rana_walk': {
        # Rana Walk NO requiere ART-03, ART-04, ART-07, ART-08
        'default': {
            'REGISTRO': {
                'required':         ['ART-01'],
                'optional':         ['ART-02'],
                'gate_for_advance': ['ART-01'],
            },
            'PREPARACION': {
                'required':         ['ART-02'],
                'optional':         ['ART-09'],
                'gate_for_advance': ['ART-02'],
            },
            'PRODUCCION': {
                'required':         [],
                'optional':         ['ART-06'],
                'gate_for_advance': [],
            },
            'DESPACHO': {
                'required':         ['ART-05', 'ART-06', 'ART-09'],
                'optional':         ['ART-10'],
                'gate_for_advance': ['ART-05', 'ART-09'],
            },
            'TRANSITO': {
                'required':         ['ART-05', 'ART-10'],
                'optional':         [],
                'gate_for_advance': ['ART-10'],
            },
            'DESTINO': {
                'required':         ['ART-10'],
                'optional':         [],
                'gate_for_advance': ['ART-10'],
            },
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
                'optional':         ['ART-09'],
                'gate_for_advance': ['ART-02', 'ART-04'],
            },
            'PRODUCCION': {
                'required':         ['ART-04', 'ART-08'],
                'optional':         ['ART-06'],
                'gate_for_advance': ['ART-04'],
            },
            'DESPACHO': {
                'required':         ['ART-05', 'ART-06', 'ART-09'],
                'optional':         ['ART-07', 'ART-10'],
                'gate_for_advance': ['ART-05', 'ART-06', 'ART-09'],
            },
            'TRANSITO': {
                'required':         ['ART-05', 'ART-10'],
                'optional':         [],
                'gate_for_advance': ['ART-10'],
            },
            'DESTINO': {
                'required':         ['ART-10'],
                'optional':         [],
                'gate_for_advance': ['ART-10'],
            },
        },
    },
}

# ---------------------------------------------------------------------------
# 3. Fallback genérico: solo REGISTRO con ART-01
# ---------------------------------------------------------------------------
GENERIC_REGISTRO: dict = {
    'REGISTRO': {
        'required':         ['ART-01'],
        'optional':         [],
        'gate_for_advance': ['ART-01'],
    },
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


# ---------------------------------------------------------------------------
# 4. resolve_artifact_policy(expediente) → dict JSON-serializable
# ---------------------------------------------------------------------------
def resolve_artifact_policy(expediente) -> dict:
    """
    Calcula dinámicamente la política de artefactos para un expediente.

    Lógica:
    - Sin proformas completadas  → retorna policy REGISTRO del brand (o GENERIC si brand desconocida)
    - Brand desconocida con proformas → retorna GENERIC_REGISTRO
    - Con proformas → merge de policies por mode de cada proforma
      - required gana sobre optional
      - gate_for_advance siempre ⊆ required
    - Output siempre JSON-serializable (listas, no sets)

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

    # Sin proformas → policy REGISTRO del brand o fallback genérico
    if not proformas:
        if brand_policy:
            # Tomar el primer mode disponible para el brand (default o primero)
            first_mode = next(iter(brand_policy))
            registro = brand_policy[first_mode].get('REGISTRO')
            if registro:
                return {'REGISTRO': _as_lists(registro)}
        return dict(GENERIC_REGISTRO)

    # Brand desconocida con proformas → fallback genérico
    if not brand_policy:
        return dict(GENERIC_REGISTRO)

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

    # Fallback si el merge quedó vacío (todos los modes eran desconocidos)
    if not merged:
        return dict(GENERIC_REGISTRO)

    # Normalización post-merge
    for state in merged:
        # required gana sobre optional
        merged[state]['optional'] -= merged[state]['required']
        # gate_for_advance siempre ⊆ required
        merged[state]['gate_for_advance'] &= merged[state]['required']

    # Convertir sets a sorted lists para determinismo JSON
    return {
        state: {
            'required':         sorted(merged[state]['required']),
            'optional':         sorted(merged[state]['optional']),
            'gate_for_advance': sorted(merged[state]['gate_for_advance']),
        }
        for state in merged
    }


def _as_lists(rules: dict) -> dict:
    """Convierte listas de una policy individual a listas ordenadas."""
    return {
        'required':         sorted(rules.get('required', [])),
        'optional':         sorted(rules.get('optional', [])),
        'gate_for_advance': sorted(rules.get('gate_for_advance', [])),
    }
