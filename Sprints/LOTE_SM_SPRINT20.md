# LOTE_SM_SPRINT20 — Modelo Proformas + ArtifactPolicy Backend
id: LOTE_SM_SPRINT20
version: 1.6
visibility: [INTERNAL]
domain: Plataforma (IDX_PLATAFORMA)
status: DRAFT — Pendiente aprobación CEO
stamp: DRAFT v1.6 — 2026-03-30
tipo: Lote ruteado (ref → PLB_ORCHESTRATOR §E)
sprint: 20
priority: P0
depends_on: LOTE_SM_SPRINT19 (EN EJECUCIÓN), LOTE_SM_SPRINT18 (DONE v3.5)
refs: DIRECTRIZ_ARTEFACTOS_MODULARES (VIGENTE),
      ENT_OPS_STATE_MACHINE (FROZEN v1.2.2),
      POL_ARTIFACT_CONTRACT (VIGENTE v1.0),
      ARTIFACT_REGISTRY (VIGENTE v1.1),
      ENT_PLAT_SEGURIDAD,
      ENT_GOB_DECISIONES (DEC-EXP-01 a DEC-EXP-05, DEC-SIZE-01)

changelog:
  - v1.0 (2026-03-30): Compilación inicial desde ROADMAP_EXTENDIDO_POST_DIRECTRIZ (Sprint 20). 12 items, 4 fases. Absorbe DIRECTRIZ_ARTEFACTOS_MODULARES HR-7 a HR-15, implementación backend Parte V completa.
  - v1.1 (2026-03-30): Fixes auditoría R1 (ChatGPT 8.3/10 — 10 hallazgos). H1: resolve_artifact_policy() +normalización post-merge (required gana sobre optional, gate⊆required). H2: brand desconocido → fallback REGISTRO genérica (alineado código/tests/reglas). H3: +path de transición explícito para expedientes legacy (no cruzan C5 sin remediación manual). H4: reassign-line captura old_proforma_id ANTES del cambio. H5: reassign-line +transaction.atomic()+select_for_update(). H6: payload.lines eliminado de contrato ART-02 — relación vive solo en EPL.proforma FK. H7: create_proforma +validación line_ids (requested vs found, dedup, assigned_count real). H8: C1 especificado como extensión del handler existente (no reescritura). H9: +tabla de transiciones mode completa (default↔b↔c) con semántica y tests. H10: tests renumerados a 25 backend reales (eliminados items frontend fantasma).
  - v1.2 (2026-03-30): Fixes auditoría R2 (ChatGPT 8.9/10 — 8 hallazgos). H1: regresión fix H6 — DONE S20-04 limpiado (ya no habla de actualizar EPL desde lines). H2: resolve_artifact_policy() +early-return si brand_policy vacío con proformas + fallback final si merged vacío. H3: select_for_update() en Expediente en reassign-line y create_proforma (proteger gate de status). H4: +validación mode por brand (BRAND_ALLOWED_MODES) en create_proforma y change_proforma_mode. H5: operated_by siempre presente (no condicional a mode). H6: convención legacy expandida — frontend NO depende de artifact_policy para estados > REGISTRO en legacy. H7: pseudocódigo create_proforma limpiado (doble transaction.atomic unificado, basura eliminada). H8: metadatos alineados (changelog corregido, stamp actualizado).
  - v1.3 (2026-03-30): Fixes auditoría R3 (ChatGPT 9.2/10 — 5 hallazgos). H1: void_map simplificado — transiciones default↔mode_b/c son inválidas bajo BRAND_ALLOWED_MODES (la validación las rechaza antes); eliminadas de la tabla. Test 18 reemplazado por test de rechazo. H2: change_proforma_mode() +select_for_update en proforma, expediente y artefactos afectados + re-verificación de mode dentro de transacción. H3: BRAND_ALLOWED_MODES centralizada en artifact_policy.py (una sola fuente de verdad, importar en endpoints). H4: line_ids validación de tipo (list[int]) antes de set/dedup, null→[] sin explotar. H5: +2 tests (line_ids=null, line_ids=string) + test 18/27 alineados con política de brand.
  - v1.4 (2026-03-30): Fixes auditoría R4 (ChatGPT 9.4/10 — 3 hallazgos). H1: import path BRAND_ALLOWED_MODES unificado a artifact_policy.py en todo el lote. H2: line_ids validación estricta con try/except→ValidationError, rechazo explícito de bool. H3: +test 31 (mode_c→mode_b happy path con void ART-09).
  - v1.5 (2026-03-30): Fixes auditoría R5 (ChatGPT 9.3/10 — 3 hallazgos). H1: regresión R4-H2 — line_ids reescrito sin casts mágicos (isinstance checks secuenciales: list→no bool→solo int→dedup). H2: +3 tests (bool en lista, string en lista, brand desconocida). H3: unknown brand rechazada en endpoints mutantes (create_proforma + change_mode) con ValidationError explícito.
  - v1.6 (2026-03-30): Fixes auditoría R6 (ChatGPT 9.5/10 APROBADO — 2 hallazgos). H1: regresión R3-H2 — early return "mismo modo" movido DENTRO del transaction.atomic() después del select_for_update(); old_mode se lee de la proforma re-fetched, no del objeto stale. H2: +test 35 (change_mode brand desconocida). Total: 35 tests.

---

## Contexto

Sprint 20 es el primero que implementa la **DIRECTRIZ_ARTEFACTOS_MODULARES** — el cambio de paradigma donde la proforma (ART-02) se convierte en la unidad operativa del expediente. Hasta Sprint 19 inclusive, el expediente era monolítico: un mode, un set de artefactos, líneas planas. Sprint 20 lo transforma en un contenedor de N proformas independientes, cada una con su mode, su cadena de artefactos, y sus líneas.

**Cambio de paradigma en 3 frases:**
1. El expediente pasa de contenedor monolítico a contenedor de proformas.
2. Cada proforma tiene su mode (B o C) independiente — un expediente puede tener proformas mixtas.
3. El backend calcula qué artefactos aplican (ArtifactPolicy) y el frontend solo renderiza lo que recibe.

**Estado post-Sprint 19 (asumido DONE):**
- Frontend expedientes completo (formularios, detalle por estado, merge/split, pagos)
- Motor dimensional plataforma funcional (`sizing/` app, 6 modelos)
- EPL con FK a BrandSKU + ProductMaster
- 5 endpoints PATCH por estado, CRUD FactoryOrder, merge/split, pagos
- Hook post_command_hooks en dispatcher
- Bundle detalle con product_lines + factory_orders + pagos
- Tab Tallas en Brand Console

**Lo que falta (scope de este sprint):**
- 0 soporte para múltiples proformas por expediente (HR-7)
- 0 mode a nivel de proforma — está a nivel expediente (HR-8/9)
- 0 ArtifactPolicy calculada por backend (HR-1/2)
- C1 requiere OC completa — debería solo requerir client+brand (HR-13)
- Líneas pertenecen al expediente directo — deberían pertenecer a proforma (HR-10)
- Artefactos post-proforma no se vinculan a su proforma (HR-11)
- ART-05 no soporta multi-proforma (HR-12)
- Frontend decide qué artefactos mostrar — debería ser backend-driven (HR-1)

---

## Decisiones ya resueltas (NO preguntar de nuevo)

| Decisión | Ref | Detalle |
|----------|-----|---------|
| `factory_order_number` genérico + `FactoryOrder` relacional | DEC-EXP-01 | Multi-fabricante. Implementado en S17. |
| Merge master/follower elegido por CEO | DEC-EXP-02 | No automático. |
| Crédito = snapshot + recálculo local | DEC-EXP-03 | No crédito vivo. |
| EPL FK a ProductMaster (no texto libre) | DEC-EXP-04 | Implementado en S17. |
| PATCH por estado son ADICIONALES a commands | DEC-EXP-05 | No reemplazan commands. |
| Motor dimensional genérico de plataforma | DEC-SIZE-01 | App `sizing/`. Implementado en S18. |

## Decisiones nuevas Sprint 20

| Decisión | Ref | Detalle |
|----------|-----|---------|
| ArtifactPolicy como constante Python | SG-01 | Arranca como dict en `artifact_policy.py`. Migra a DB (`BrandWorkflowPolicy`) en Sprint 23. Razón: iterar rápido sin UI de configuración. |
| ART-05 multi-proforma | SG-04 / HR-12 | M2M vía array de IDs en payload JSON de ArtifactInstance(ART-05). No modelo M2M explícito — el payload ya es JSONField. |
| Void automático por cambio de modo | SG-05 | Si proforma cambia mode_b→mode_c: void ART-10. Si mode_c→mode_b: void ART-09. Requiere `confirm_void=true` en payload. EventLog registra. |
| `operated_by` = siempre MWT por ahora | SG-06 | CharField con default `"muito_work_limitada"`. No FK a LegalEntity. Si aparece otra subsidiaria, se migra. |
| C1 flexible: solo client_id + brand_id | HR-13 | OC, líneas, proformas son opcionales en creación. Backward compatible. |
| Mode a nivel proforma, no expediente | HR-8/9 | `payload.mode` en ArtifactInstance(ART-02). Enum: `mode_b`, `mode_c`, `default`. |

---

## Convenciones Sprint 20

1. **State machine FROZEN.** No se modifican estados ni transiciones. Solo se extiende cómo se resuelven artefactos dentro de los estados existentes.
2. **Backward compat obligatorio.** C1 sin campos nuevos sigue funcionando. Bundle sin proformas retorna policy genérica REGISTRO. Expedientes creados pre-S20 siguen operando.
3. **Additive-only.** Toda migración agrega campos/FK nullable. 0 AlterField, 0 RemoveField.
4. **Proforma = ArtifactInstance con artifact_type='ART-02'.** No se crea modelo nuevo. Se extiende el modelo existente con FK y validaciones.
5. **Tests cubren pre-S20 y post-S20.** Expedientes sin proformas (legacy) y expedientes con N proformas (nuevo) deben funcionar.
6. **Path de transición legacy.** Expedientes creados antes de S20 siguen operando normalmente en su estado actual. Sin embargo, **no pueden cruzar C5 sin remediación**: el CEO debe asignarles al menos una proforma (ART-02) con mode y líneas asignadas. Esto es intencional — la directriz establece que C5 requiere proformas. No existe backfill automático; la remediación es manual vía los nuevos endpoints de crear proforma + reassign-line. **Regla frontend (R2-H6):** mientras existan expedientes legacy sin proformas en estados > REGISTRO, el frontend NO debe depender de `artifact_policy` del bundle para esos expedientes. Para ellos, `artifact_policy` retornará solo REGISTRO genérica independientemente de su estado real. Sprint 20B debe implementar un fallback visual para este caso (ej: mostrar artefactos según la lógica anterior hasta que se remedien).

---

## FASE 0 — Modelo de datos (migración aditiva)

### S20-01: FK `proforma` nullable en ExpedienteProductLine

**Agente:** AG-02 Backend
**Dependencia:** Ninguna interna
**Prioridad:** P0 — bloqueante para S20-06 y toda Fase 2
**Acción:** AddField

**Archivos a tocar:**
- `backend/apps/expedientes/models.py` (modelo ExpedienteProductLine)
- `backend/apps/expedientes/admin.py` (inline updated)

**Archivos prohibidos:**
- `backend/apps/expedientes/services/state_machine/` (FROZEN, no tocar handlers)

**Detalle:**

```python
# En ExpedienteProductLine — agregar campo:
proforma = models.ForeignKey(
    'ArtifactInstance',
    null=True,
    blank=True,
    limit_choices_to={'artifact_type': 'ART-02'},
    on_delete=models.SET_NULL,
    related_name='proforma_lines',
    help_text="Proforma (ART-02) a la que pertenece esta línea. "
              "Null = línea huérfana, pendiente de asignación."
)
```

**Reglas:**
- `on_delete=SET_NULL` — si se borra la proforma, la línea queda huérfana (no se borra)
- `related_name='proforma_lines'` — no usar `lines` para evitar conflicto con `expediente.lines`
- Se mantiene `expediente` FK directo — no se elimina. Sirve para queries rápidas y backward compat.
- Líneas creadas antes de S20 tendrán `proforma=NULL` — es correcto, son legacy.

**Criterio de done:**
- [ ] Campo `proforma` existe en `ExpedienteProductLine`, nullable
- [ ] Migración generada es `AddField` solamente
- [ ] `ExpedienteProductLine.objects.filter(proforma__isnull=True)` retorna líneas legacy
- [ ] Admin muestra campo proforma en inline

---

### S20-02: FK `parent_proforma` nullable en ArtifactInstance

**Agente:** AG-02 Backend
**Dependencia:** Ninguna interna
**Prioridad:** P0 — bloqueante para S20-07 y Fase 1
**Acción:** AddField

**Archivos a tocar:**
- `backend/apps/expedientes/models.py` (modelo ArtifactInstance)

**Detalle:**

```python
# En ArtifactInstance — agregar campo:
parent_proforma = models.ForeignKey(
    'self',
    null=True,
    blank=True,
    limit_choices_to={'artifact_type': 'ART-02'},
    on_delete=models.SET_NULL,
    related_name='child_artifacts',
    help_text="Proforma (ART-02) padre de este artefacto. "
              "Ej: ART-04 (SAP) vinculado a proforma PF-001. "
              "Null = artefacto a nivel expediente (ART-01, ART-11, ART-12)."
)
```

**Reglas HR-11:**
- ART-04 (SAP) → vinculado a UNA proforma
- ART-05 (embarque) → vinculado a UNA proforma via parent_proforma (puede vincular más vía payload, ver S20-03)
- ART-09 (factura MWT) → vinculado a UNA proforma
- ART-10 (factura comisión) → vinculado a UNA proforma
- **Excepciones a nivel expediente (parent_proforma=NULL):** ART-01 (OC), ART-11 (costos), ART-12 (compensación)

**Criterio de done:**
- [ ] Campo `parent_proforma` existe en `ArtifactInstance`, nullable
- [ ] Migración generada es `AddField` solamente
- [ ] `ArtifactInstance.objects.filter(parent_proforma__isnull=False)` retorna artefactos vinculados a proforma
- [ ] ArtifactInstance creados pre-S20 tienen `parent_proforma=NULL` (correcto)

---

### S20-03: ART-05 multi-proforma vía payload (HR-12)

**Agente:** AG-02 Backend
**Dependencia:** S20-02
**Prioridad:** P1
**Acción:** Validación en serializer, no migración

**Archivos a tocar:**
- `backend/apps/expedientes/serializers.py` (validación payload ART-05)
- `backend/apps/expedientes/services/artifact_policy.py` (nueva, ver S20-05)

**Detalle:**

ART-05 (embarque) puede combinar líneas de múltiples proformas cuando viajan juntas (HR-12). El `parent_proforma` FK de S20-02 apunta a la proforma "principal". Las proformas adicionales se registran en `payload.linked_proformas`:

```python
# Payload de ArtifactInstance con artifact_type='ART-05':
{
    "artifact_type": "ART-05",
    "payload": {
        "awb_number": "123-45678901",
        "carrier": "DHL",
        "linked_proformas": [proforma_id_1, proforma_id_2],  # IDs de ART-02 vinculadas
        # ... otros campos existentes
    }
}
```

**Validación en serializer:**
- Todos los IDs en `linked_proformas` deben ser ArtifactInstances con `artifact_type='ART-02'` del mismo expediente
- `parent_proforma` FK debe ser uno de los IDs en `linked_proformas`

**Criterio de done:**
- [ ] ART-05 acepta `linked_proformas` en payload
- [ ] Validación: todos los IDs son ART-02 del mismo expediente
- [ ] ART-05 puede vincular 1 o N proformas
- [ ] Test: crear ART-05 con 2 proformas → OK

---

### S20-04: Validar mode en payload de ART-02 (HR-8/9)

**Agente:** AG-02 Backend
**Dependencia:** Ninguna interna
**Prioridad:** P0
**Acción:** Validación en serializer + servicio

**Archivos a tocar:**
- `backend/apps/expedientes/serializers.py`
- `backend/apps/expedientes/services/` (helper de validación)

**Detalle:**

El mode vive en `payload.mode` de ArtifactInstance con `artifact_type='ART-02'`. No como campo flat en Expediente.

```python
# Payload de ART-02 (proforma):
{
    "artifact_type": "ART-02",
    "payload": {
        "proforma_number": "PF-001-2026",
        "mode": "mode_c",                        # REQUERIDO — enum: mode_b, mode_c, default
        "operated_by": "muito_work_limitada",     # CharField, default MWT
        # NOTA (H6 auditoría R1): payload NO almacena líneas.
        # La relación línea→proforma vive SOLO en EPL.proforma FK (S20-01).
        # Esto evita doble fuente de verdad entre payload.lines y EPL.proforma.
    }
}
```

**Validación:**
- `mode` es campo requerido en payload de ART-02. Valores: `mode_b`, `mode_c`, `default`
- `operated_by` siempre presente en payload con default `"muito_work_limitada"`. No es condicional al mode — se almacena siempre para trazabilidad. En mode_b el valor registra quién operó aunque sea comisión.
- Las líneas se vinculan a la proforma exclusivamente vía `EPL.proforma` FK (S20-01). NO vía payload.
- Al completar ART-02: no se modifican EPL automáticamente. Las líneas se asignan explícitamente vía endpoint `create_proforma` (S20-11) o `reassign-line` (S20-09).

**Regla HR-9:** ART-03 (Decisión Modo) ahora se aplica a cada ART-02, no al expediente. CEO decide mode por proforma. Una proforma puede cambiar de B a C sin afectar las demás.

**Criterio de done:**
- [ ] ART-02 requiere `mode` en payload (validación falla sin él)
- [ ] Valores válidos: `mode_b`, `mode_c`, `default`
- [ ] `operated_by` siempre presente en payload con default `"muito_work_limitada"`
- [ ] ART-02 NO modifica EPL automáticamente; líneas se asignan vía `create_proforma` (S20-11) o `reassign-line` (S20-09)
- [ ] Dos ART-02 del mismo expediente pueden tener modos distintos
- [ ] Test: crear ART-02 sin mode → error. Con mode_b → OK. Con mode_c → OK.

---

## FASE 1 — ArtifactPolicy engine

### S20-05: Constante ARTIFACT_POLICY y servicio resolve_artifact_policy()

**Agente:** AG-02 Backend
**Dependencia:** S20-04 (mode en proforma)
**Prioridad:** P0 — bloqueante para S20-07
**Acción:** Crear archivo nuevo

**Archivos a tocar (CREAR):**
- `backend/apps/expedientes/services/artifact_policy.py`

**Archivos prohibidos:**
- `backend/apps/expedientes/services/state_machine/` (FROZEN)

**Detalle:**

```python
# backend/apps/expedientes/services/artifact_policy.py

# Constante centralizada — importar desde aquí en todos los endpoints (R3-H3)
# from .artifact_policy import BRAND_ALLOWED_MODES
BRAND_ALLOWED_MODES = {
    'marluvas': ('mode_b', 'mode_c'),
    'rana_walk': ('default',),
    'tecmater': ('default',),
}

ARTIFACT_POLICY = {
    "marluvas": {
        "mode_b": {
            "REGISTRO":     {"required": ["ART-01", "ART-02"], "optional": ["ART-03"], "gate_for_advance": ["ART-01", "ART-02"]},
            "PRODUCCION":   {"required": [], "optional": [], "gate_for_advance": []},
            "PREPARACION":  {"required": ["ART-05", "ART-06", "ART-07"], "optional": ["ART-08"], "gate_for_advance": ["ART-05", "ART-06", "ART-07"]},
            "EN_DESTINO":   {"required": ["ART-10"], "optional": ["ART-12"], "gate_for_advance": ["ART-10"]},
        },
        "mode_c": {
            "REGISTRO":     {"required": ["ART-01", "ART-02"], "optional": ["ART-03"], "gate_for_advance": ["ART-01", "ART-02"]},
            "PRODUCCION":   {"required": [], "optional": [], "gate_for_advance": []},
            "PREPARACION":  {"required": ["ART-05", "ART-06", "ART-07"], "optional": ["ART-08"], "gate_for_advance": ["ART-05", "ART-06", "ART-07"]},
            "EN_DESTINO":   {"required": ["ART-09"], "optional": ["ART-12"], "gate_for_advance": ["ART-09"]},
        },
    },
    "rana_walk": {
        "default": {
            "REGISTRO":     {"required": ["ART-01", "ART-02"], "optional": [], "gate_for_advance": ["ART-01", "ART-02"]},
            "DESPACHO":     {"required": ["ART-05", "ART-06"], "optional": [], "gate_for_advance": ["ART-05", "ART-06"]},
            "EN_DESTINO":   {"required": ["ART-09"], "optional": [], "gate_for_advance": ["ART-09"]},
        },
    },
    "tecmater": {
        "default": {
            "REGISTRO":     {"required": ["ART-01", "ART-02"], "optional": [], "gate_for_advance": ["ART-01", "ART-02"]},
            "PREPARACION":  {"required": ["ART-05", "ART-06", "ART-07"], "optional": ["ART-08"], "gate_for_advance": ["ART-05", "ART-06", "ART-07"]},
            "EN_DESTINO":   {"required": ["ART-09"], "optional": [], "gate_for_advance": ["ART-09"]},
        },
    },
}


def resolve_artifact_policy(expediente) -> dict:
    """
    Calcula la ArtifactPolicy para un expediente basándose en sus proformas.
    
    Sin proformas → policy genérica REGISTRO (solo client+brand necesarios).
    Con proformas → unión de policies de todas las proformas según su mode.
    
    Retorna dict serializable: {estado: {required: [...], optional: [...], gate_for_advance: [...]}}
    """
    brand_slug = expediente.brand.slug
    brand_policy = ARTIFACT_POLICY.get(brand_slug, {})
    
    # Fallback genérico para brand desconocido (R2-H2)
    GENERIC_REGISTRO = {"REGISTRO": {
        "required": ["ART-01", "ART-02"],
        "optional": [],
        "gate_for_advance": ["ART-01", "ART-02"]
    }}
    
    proformas = expediente.artifacts.filter(
        artifact_type='ART-02',
        status='COMPLETED'
    )
    
    if not proformas.exists():
        # Sin proformas — retornar policy genérica de REGISTRO
        default = brand_policy.get("default", {})
        return {"REGISTRO": default.get("REGISTRO", GENERIC_REGISTRO["REGISTRO"])}
    
    # Brand desconocido CON proformas → misma policy genérica (R2-H2)
    if not brand_policy:
        return GENERIC_REGISTRO
    
    # Unir policies de todas las proformas según su modo
    merged = {}
    for pf in proformas:
        mode = pf.payload.get('mode', 'default')
        pf_policy = brand_policy.get(mode, brand_policy.get("default", {}))
        for state, config in pf_policy.items():
            if state not in merged:
                merged[state] = {
                    "required": set(),
                    "optional": set(),
                    "gate_for_advance": set()
                }
            merged[state]["required"].update(config.get("required", []))
            merged[state]["optional"].update(config.get("optional", []))
            merged[state]["gate_for_advance"].update(config.get("gate_for_advance", []))
    
    # Normalización post-merge (H1 auditoría R1):
    # 1. required gana sobre optional — si un artefacto está en ambos, se queda solo en required
    # 2. gate_for_advance debe ser subconjunto de required
    for state, config in merged.items():
        config["optional"] -= config["required"]  # required gana
        config["gate_for_advance"] &= config["required"]  # gate ⊆ required
    
    # Fallback final: si merged quedó vacío (mode no encontrado en brand_policy), REGISTRO genérica
    if not merged:
        return GENERIC_REGISTRO
    
    # Convertir sets a listas ordenadas para serialización determinista
    return {
        state: {
            key: sorted(list(value))
            for key, value in config.items()
        }
        for state, config in merged.items()
    }
```

**Reglas:**
- `brand.slug` debe matchear keys del dict: `"marluvas"`, `"rana_walk"`, `"tecmater"`. Verificar que Brand.slug esté normalizado.
- Si brand no existe en el dict → fallback a REGISTRO genérica (misma que sin proformas). No retornar vacío.
- Si mode de proforma no existe en brand → fallback a `"default"` key del brand.
- **Normalización post-merge:** required gana sobre optional (set difference). gate_for_advance es siempre subconjunto de required (set intersection).
- Sets para merge (evitar duplicados) → sorted lists para determinismo JSON.
- **No tocar state machine.** Esta función es de lectura — calcula qué artefactos aplican, no modifica estados.

**Criterio de done:**
- [ ] Archivo `artifact_policy.py` existe en `services/`
- [ ] `ARTIFACT_POLICY` contiene 4 configs: marluvas/mode_b, marluvas/mode_c, rana_walk/default, tecmater/default
- [ ] `resolve_artifact_policy()` con 0 proformas → policy REGISTRO genérica
- [ ] `resolve_artifact_policy()` con 1 proforma mode_b → policy mode_b completa
- [ ] `resolve_artifact_policy()` con 2 proformas mixed → unión correcta, optional no contiene items de required
- [ ] `resolve_artifact_policy()` con brand desconocido → fallback a REGISTRO genérica (no vacío)
- [ ] gate_for_advance es siempre subconjunto de required
- [ ] Rana Walk policy NO incluye ART-03, ART-04, ART-07, ART-08
- [ ] Output es JSON serializable (listas, no sets)

---

### S20-06: Bundle retorna artifact_policy calculada

**Agente:** AG-02 Backend
**Dependencia:** S20-05
**Prioridad:** P0
**Acción:** Extender endpoint existente

**Archivos a tocar:**
- `backend/apps/expedientes/views.py` (o `viewsets.py`) — GET `/api/ui/expedientes/{id}/`
- `backend/apps/expedientes/serializers.py` — BundleSerializer

**Detalle:**

Agregar al bundle de detalle:

```python
# En el serializer del bundle (GET /api/ui/expedientes/{id}/):
from .services.artifact_policy import resolve_artifact_policy

class ExpedienteBundleSerializer(serializers.ModelSerializer):
    # ... campos existentes ...
    artifact_policy = serializers.SerializerMethodField()
    
    def get_artifact_policy(self, obj):
        return resolve_artifact_policy(obj)
```

**Respuesta ejemplo:**
```json
{
    "id": 42,
    "status": "REGISTRO",
    "client": {...},
    "brand": {"slug": "marluvas", ...},
    "product_lines": [...],
    "factory_orders": [...],
    "artifact_policy": {
        "REGISTRO": {
            "required": ["ART-01", "ART-02"],
            "optional": ["ART-03"],
            "gate_for_advance": ["ART-01", "ART-02"]
        },
        "PRODUCCION": {
            "required": [],
            "optional": [],
            "gate_for_advance": []
        },
        "PREPARACION": {
            "required": ["ART-05", "ART-06", "ART-07"],
            "optional": ["ART-08"],
            "gate_for_advance": ["ART-05", "ART-06", "ART-07"]
        },
        "EN_DESTINO": {
            "required": ["ART-09", "ART-10"],
            "optional": ["ART-12"],
            "gate_for_advance": ["ART-09", "ART-10"]
        }
    }
}
```

**Criterio de done:**
- [ ] GET `/api/ui/expedientes/{id}/` retorna `artifact_policy` en el bundle
- [ ] Policy calculada dinámicamente (no hardcodeada en serializer)
- [ ] Expediente sin proformas → policy con solo REGISTRO
- [ ] Expediente con proformas → policy completa

---

## FASE 2 — C1 flexible + C5 actualizado

### S20-07: Actualizar handle_c1 — mínimo client_id + brand_id (HR-13)

**Agente:** AG-02 Backend
**Dependencia:** S20-01, S20-04
**Prioridad:** P0
**Acción:** Modificar handler existente

**Archivos a tocar:**
- `backend/apps/expedientes/services/state_machine/c_create.py` (o donde viva handle_c1)

**Archivos prohibidos:**
- ENT_OPS_STATE_MACHINE (FROZEN) — no se cambia la spec, solo la implementación de C1

**Detalle:**

El cambio en C1 es **mínimo**: se relaja la validación de campos requeridos en el handler existente (`c_create.py` o equivalente). NO se reescribe el handler completo.

**Cambio concreto:**
1. Encontrar la validación de campos requeridos en `handle_c1` (donde se valida que OC existe, o que hay líneas).
2. Mover esos campos de "requeridos" a "opcionales con default". `client_id` y `brand_id` siguen siendo requeridos.
3. El resto del handler (credit_check, creación del Expediente, EventLog, etc.) NO se toca.

```python
# ANTES (S18/S19):
# handle_c1 requiere: client_id, brand_id, oc (o purchase_order_number), etc.

# DESPUÉS (S20):
# handle_c1 requiere: client_id, brand_id
# Todo lo demás es opcional:
#   - payload.get('oc') → si viene, crea ART-01. Si no viene, no.
#   - payload.get('lines', []) → si vienen, crea EPL con proforma=None. Si no, no.
#   - payload.get('purchase_order_number') → si viene, se guarda. Si no, queda null.

# credit_check sigue ejecutándose igual — usa client_id, NO necesita OC.
# Todos los campos legacy que vengan en el payload siguen procesándose normalmente.
```

**Verificación grep pre-implementación:** Antes de modificar, AG-02 debe hacer `grep -n "required" c_create.py` para identificar exactamente qué validaciones relajan.

**Reglas:**
- `client_id` + `brand_id` son los únicos campos requeridos
- OC, líneas, todo lo demás es opcional
- credit_check existente sigue funcionando (usa client, no OC)
- POST con payload completo estilo S18 sigue funcionando — backward compat obligatorio

**Criterio de done:**
- [ ] POST con solo `{client_id, brand_id}` → crea expediente en REGISTRO
- [ ] POST con payload completo (OC + líneas) → funciona igual que antes
- [ ] credit_check se ejecuta correctamente con solo client_id
- [ ] Tests legacy siguen verdes (0 regresiones)

---

### S20-08: Actualizar validate_c5_gate (HR-13)

**Agente:** AG-02 Backend
**Dependencia:** S20-01, S20-04
**Prioridad:** P0
**Acción:** Modificar validación existente

**Archivos a tocar:**
- `backend/apps/expedientes/services/state_machine/` (donde viva la validación de C5)

**Detalle:**

```python
def validate_c5_gate(expediente):
    """
    Gate para avanzar de REGISTRO → PRODUCCION.
    Actualizado con reglas de proformas (DIRECTRIZ HR-13).
    """
    errors = []
    
    # 1. ART-01 existe y completada
    if not expediente.artifacts.filter(
        artifact_type='ART-01', status='COMPLETED'
    ).exists():
        errors.append("Falta OC del cliente (ART-01)")
    
    # 2. Al menos 1 ART-02 completada
    proformas = expediente.artifacts.filter(
        artifact_type='ART-02', status='COMPLETED'
    )
    if not proformas.exists():
        errors.append("Falta al menos una proforma (ART-02)")
    
    # 3. Todas las líneas asignadas a una proforma
    orphan_lines = expediente.lines.filter(proforma__isnull=True)
    if orphan_lines.exists():
        errors.append(
            f"{orphan_lines.count()} línea(s) sin proforma asignada"
        )
    
    # 4. Cada proforma tiene mode asignado
    for pf in proformas:
        pf_number = pf.payload.get('proforma_number', pf.id)
        if not pf.payload.get('mode'):
            errors.append(
                f"Proforma {pf_number} sin modo asignado"
            )
    
    if errors:
        raise GateError(errors)
```

**Compatibilidad:** Expedientes legacy sin proformas (creados pre-S20) fallarán C5 hasta que se les asigne proformas. Esto es correcto — la directriz establece que el expediente necesita al menos 1 proforma para avanzar.

**Criterio de done:**
- [ ] C5 con 0 proformas → error "Falta al menos una proforma"
- [ ] C5 con 1 proforma sin mode → error "sin modo asignado"
- [ ] C5 con línea sin proforma → error "línea(s) sin proforma asignada"
- [ ] C5 con todo completo → avanza a PRODUCCION normalmente
- [ ] Error messages son descriptivos (lista de todo lo que falta)

---

### S20-09: Endpoint POST reassign-line/ (HR-10)

**Agente:** AG-02 Backend
**Dependencia:** S20-01
**Prioridad:** P1
**Acción:** Crear endpoint nuevo

**Archivos a tocar:**
- `backend/apps/expedientes/views.py`
- `backend/apps/expedientes/urls.py`

**Detalle:**

```python
# POST /api/expedientes/{id}/reassign-line/
# Payload: {"line_id": 42, "target_proforma_id": 7}

@action(detail=True, methods=['post'], url_path='reassign-line')
def reassign_line(self, request, pk=None):
    with transaction.atomic():
        # Bloquear expediente para proteger validación de status (R2-H3)
        expediente = Expediente.objects.select_for_update().get(pk=pk)
        
        line_id = request.data['line_id']
        target_id = request.data['target_proforma_id']
        
        line = ExpedienteProductLine.objects.select_for_update().get(
            id=line_id, expediente=expediente
        )
        target = ArtifactInstance.objects.select_for_update().get(
            id=target_id,
            expediente=expediente,
            artifact_type='ART-02'
        )
        
        # Solo antes de PRODUCCION — validado sobre fila bloqueada
        if expediente.status != 'REGISTRO':
            raise ValidationError(
                "Líneas solo se pueden mover entre proformas en estado REGISTRO"
            )
        
        # Capturar ANTES del cambio (H4 auditoría R1)
        old_proforma_id = line.proforma_id
        
        line.proforma = target
        line.save(update_fields=['proforma'])
        
        # EventLog con old_proforma_id real
        EventLog.objects.create(
            expediente=expediente,
            event_type='line.reassigned',
            payload={
                'line_id': line.id,
                'from_proforma': old_proforma_id,
                'to_proforma': target.id
            }
        )
    
    return Response({'status': 'reassigned'})
```

**Reglas:**
- Solo en estado REGISTRO (antes de PRODUCCION — HR-10: "Se puede mover a PF-002 antes de producción")
- Ambas proformas deben pertenecer al mismo expediente
- `transaction.atomic()` + `select_for_update()` en línea y target para evitar race conditions
- EventLog captura `old_proforma_id` **antes** del cambio (no después)

**Criterio de done:**
- [ ] POST reassign-line/ mueve línea de proforma A a proforma B
- [ ] Falla si expediente no está en REGISTRO
- [ ] Falla si target no es ART-02 del mismo expediente
- [ ] EventLog registra from_proforma (valor real pre-cambio) y to_proforma
- [ ] Operación es atómica (select_for_update + transaction.atomic)

---

## FASE 3 — Void por cambio de modo + tests

### S20-10: Void automático al cambiar modo de proforma (SG-05)

**Agente:** AG-02 Backend
**Dependencia:** S20-02, S20-04
**Prioridad:** P1
**Acción:** Crear servicio nuevo

**Archivos a tocar:**
- `backend/apps/expedientes/services/proforma_mode.py` (CREAR)

**Detalle:**

```python
# backend/apps/expedientes/services/proforma_mode.py

def change_proforma_mode(proforma, new_mode, confirm_void=False, user=None):
    """
    Cambia el modo de una proforma y void artefactos incompatibles.
    
    mode_b → mode_c: void ART-10 (factura comisión) si existe
    mode_c → mode_b: void ART-09 (factura MWT) si existe
    
    Requiere confirm_void=True para ejecutar voids.
    Sin confirm_void, retorna lista de artefactos que serían voided.
    """
    # Validar new_mode es enum válido (antes del lock — falla rápido)
    if new_mode not in ('mode_b', 'mode_c', 'default'):
        raise ValidationError(f"mode inválido: '{new_mode}'. Valores: mode_b, mode_c, default")
    
    # Validar new_mode permitido para esta brand (antes del lock — falla rápido)
    # from .artifact_policy import BRAND_ALLOWED_MODES
    brand_slug = proforma.expediente.brand.slug
    allowed = BRAND_ALLOWED_MODES.get(brand_slug)
    if allowed is None:
        raise ValidationError(
            f"Brand '{brand_slug}' no está configurada en BRAND_ALLOWED_MODES."
        )
    if new_mode not in allowed:
        raise ValidationError(
            f"Brand '{brand_slug}' no acepta mode='{new_mode}'. "
            f"Valores válidos: {', '.join(allowed)}"
        )
    
    void_map = {
        ('mode_b', 'mode_c'): 'ART-10',
        ('mode_c', 'mode_b'): 'ART-09',
    }
    
    # Todo lo que depende del estado real de la proforma va DENTRO del lock (R6-H1)
    with transaction.atomic():
        # Re-fetch con lock — fuente de verdad para old_mode
        proforma = ArtifactInstance.objects.select_for_update().get(pk=proforma.pk)
        Expediente.objects.select_for_update().get(pk=proforma.expediente_id)
        
        old_mode = proforma.payload.get('mode')  # leído DESPUÉS del lock
        
        if old_mode == new_mode:
            return {'changed': False, 'message': 'Mismo modo'}
        
        artifact_to_void = void_map.get((old_mode, new_mode))
        
        affected = []
        if artifact_to_void:
            affected = list(
                ArtifactInstance.objects.select_for_update().filter(
                    parent_proforma=proforma,
                    artifact_type=artifact_to_void,
                    status='COMPLETED'
                )
            )
    
        if affected and not confirm_void:
            return {
                'changed': False,
                'requires_confirmation': True,
                'artifacts_to_void': [
                    {'id': a.id, 'type': a.artifact_type, 'status': a.status}
                    for a in affected
                ]
            }
        
        # Void artefactos incompatibles
        for artifact in affected:
            artifact.status = 'VOIDED'
            artifact.payload['void_reason'] = f'Mode changed from {old_mode} to {new_mode}'
            artifact.payload['voided_by'] = user.id if user else None
            artifact.save(update_fields=['status', 'payload'])
            
            EventLog.objects.create(
                expediente=proforma.expediente,
                event_type='artifact.voided',
                payload={
                    'artifact_id': artifact.id,
                    'artifact_type': artifact.artifact_type,
                    'reason': f'Proforma mode changed {old_mode}→{new_mode}'
                }
            )
        
        # Cambiar mode
        proforma.payload['mode'] = new_mode
        proforma.save(update_fields=['payload'])
        
        EventLog.objects.create(
            expediente=proforma.expediente,
            event_type='proforma.mode_changed',
            payload={
                'proforma_id': proforma.id,
                'old_mode': old_mode,
                'new_mode': new_mode,
                'voided_artifacts': [a.id for a in affected]
            }
        )
    
    return {
        'changed': True,
        'old_mode': old_mode,
        'new_mode': new_mode,
        'voided': [a.id for a in affected]
    }
```

**Endpoint:**

```python
# PATCH /api/expedientes/{id}/proforma/{pf_id}/change-mode/
# Payload: {"new_mode": "mode_c", "confirm_void": true}
```

**Criterio de done:**
- [ ] Cambiar mode_b→mode_c: void ART-10 si existe
- [ ] Cambiar mode_c→mode_b: void ART-09 si existe
- [ ] Cambiar marluvas mode_b→default: rechazado por BRAND_ALLOWED_MODES
- [ ] Cambiar rana_walk default→mode_c: rechazado por BRAND_ALLOWED_MODES
- [ ] Sin confirm_void → retorna lista de artefactos afectados, no ejecuta
- [ ] Con confirm_void=true → ejecuta void + cambia mode
- [ ] Proforma, expediente y artefactos afectados bloqueados con select_for_update
- [ ] Re-verifica mode actual dentro de la transacción (anti-race)
- [ ] EventLog registra void y cambio
- [ ] Artefactos voided quedan con status='VOIDED' + razón en payload

---

### S20-11: Endpoint POST crear proforma

**Agente:** AG-02 Backend
**Dependencia:** S20-04, S20-05
**Prioridad:** P0
**Acción:** Crear endpoint nuevo

**Archivos a tocar:**
- `backend/apps/expedientes/views.py`
- `backend/apps/expedientes/urls.py`

**Detalle:**

```python
# POST /api/expedientes/{id}/proformas/
# Payload: {
#     "proforma_number": "PF-001-2026",
#     "mode": "mode_c",
#     "operated_by": "muito_work_limitada",
#     "line_ids": [1, 2, 3]
# }

@action(detail=True, methods=['post'], url_path='proformas')
def create_proforma(self, request, pk=None):
    mode = request.data.get('mode')
    if mode not in ('mode_b', 'mode_c', 'default'):
        raise ValidationError("mode debe ser mode_b, mode_c o default")
    
    with transaction.atomic():
        # Bloquear expediente para proteger validación de status (R2-H3)
        expediente = Expediente.objects.select_for_update().get(pk=pk)
        
        # Solo en REGISTRO — validado sobre fila bloqueada
        if expediente.status != 'REGISTRO':
            raise ValidationError("Proformas solo se crean en estado REGISTRO")
        
        # Validar mode por brand (constante en artifact_policy.py — R4-H1)
        # from .artifact_policy import BRAND_ALLOWED_MODES
        brand_slug = expediente.brand.slug
        allowed = BRAND_ALLOWED_MODES.get(brand_slug)
        if allowed is None:
            raise ValidationError(
                f"Brand '{brand_slug}' no está configurada en BRAND_ALLOWED_MODES. "
                "Contactar arquitecto para agregar soporte."
            )
        if mode not in allowed:
            raise ValidationError(
                f"Brand '{brand_slug}' no acepta mode='{mode}'. "
                f"Valores válidos: {', '.join(allowed)}"
            )
        
        proforma = ArtifactInstance.objects.create(
            expediente=expediente,
            artifact_type='ART-02',
            status='COMPLETED',
            payload={
                'proforma_number': request.data.get(
                    'proforma_number',
                    f'PF-{expediente.id}-{timezone.now().strftime("%Y%m%d%H%M")}'
                ),
                'mode': mode,
                'operated_by': request.data.get('operated_by', 'muito_work_limitada'),
            }
        )
        
        # Asignar líneas si se proporcionan (R5-H1: validación estricta sin casts)
        raw_line_ids = request.data.get('line_ids')
        if raw_line_ids is None:
            raw_line_ids = []
        if not isinstance(raw_line_ids, list):
            raise ValidationError("line_ids debe ser una lista de enteros")
        if any(isinstance(x, bool) for x in raw_line_ids):
            raise ValidationError("line_ids no acepta valores booleanos")
        if any(not isinstance(x, int) for x in raw_line_ids):
            raise ValidationError("line_ids debe contener solo enteros (no strings ni otros tipos)")
        line_ids = list(set(raw_line_ids))  # dedup después de validar tipo
        assigned_count = 0
        if line_ids:
            lines = ExpedienteProductLine.objects.filter(
                id__in=line_ids,
                expediente=expediente
            ).select_for_update()
            
            # Verificar que TODOS los IDs solicitados existen
            found_ids = set(lines.values_list('id', flat=True))
            missing_ids = set(line_ids) - found_ids
            if missing_ids:
                raise ValidationError(
                    f"Líneas no encontradas en este expediente: {sorted(missing_ids)}"
                )
            
            # Verificar que ninguna línea ya tiene proforma
            already_assigned = lines.filter(proforma__isnull=False)
            if already_assigned.exists():
                raise ValidationError(
                    f"Líneas ya asignadas a otra proforma: "
                    f"{list(already_assigned.values_list('id', flat=True))}"
                )
            
            assigned_count = lines.update(proforma=proforma)
        
        EventLog.objects.create(
            expediente=expediente,
            event_type='proforma.created',
            payload={
                'proforma_id': proforma.id,
                'mode': mode,
                'assigned_count': assigned_count
            }
        )
    
    return Response(ProformaSerializer(proforma).data, status=201)
```

**Criterio de done:**
- [ ] POST crea ART-02 con mode y operated_by en payload
- [ ] Valida mode por brand (marluvas: mode_b/mode_c, rana_walk/tecmater: default)
- [ ] Falla si mode no permitido para la brand del expediente
- [ ] Asigna líneas si se proporcionan (con dedup + validación IDs)
- [ ] Falla si línea no existe o ya asignada a otra proforma
- [ ] Solo funciona en REGISTRO (validado con select_for_update en expediente)
- [ ] EventLog registra creación con assigned_count real
- [ ] Proforma tiene proforma_number auto-generado si no se proporciona

---

### S20-12: Tests completos

**Agente:** AG-02 Backend
**Dependencia:** Todos los items anteriores
**Prioridad:** P0
**Acción:** Crear tests

**Archivos a tocar:**
- `backend/apps/expedientes/tests/test_proformas.py` (CREAR)
- `backend/apps/expedientes/tests/test_artifact_policy.py` (CREAR)

**Tests requeridos (Parte X de la directriz + H10 auditoría R1):**

```
1. Crear expediente sin OC (solo client_id + brand_id) → se crea vacío en REGISTRO ✓
2. Crear 2 proformas en mismo expediente → PF-001 mode_b, PF-002 mode_c ✓
3. Asignar líneas a proformas vía create_proforma → EPL.proforma actualizado ✓
4. Intentar C5 con línea sin proforma → gate bloquea con mensaje descriptivo ✓
5. Expediente Rana Walk → policy NO incluye ART-03, ART-04, ART-08 ✓
6. Reassign-line en estado REGISTRO → OK, EventLog con from/to correcto ✓
7. Reassign-line en estado PRODUCCION → error ✓
```

**Tests adicionales:**
```
8. resolve_artifact_policy() con 0 proformas → policy REGISTRO genérica
9. resolve_artifact_policy() con 2 proformas mixed mode → unión correcta, optional no contiene items de required
10. resolve_artifact_policy() con brand desconocido → fallback REGISTRO genérica
11. resolve_artifact_policy() normalización: artefacto en required+optional → solo en required
12. resolve_artifact_policy() gate_for_advance ⊆ required siempre
13. C1 con solo client_id + brand_id → OK (backward compat)
14. C1 con payload completo (OC + líneas, estilo S18) → funciona igual (backward compat)
15. ART-05 con linked_proformas de 2 proformas → OK
16. ART-05 con proforma de otro expediente → error
17. Cambiar mode_b → mode_c → void ART-10 si existe
18. change_mode marluvas de mode_b a default → rechazado por BRAND_ALLOWED_MODES (R3-H1)
19. Cambiar mode sin confirm_void → retorna preview, no ejecuta
20. Crear proforma con line_id inexistente → error
21. Crear proforma con línea ya asignada → error
22. Crear proforma con line_ids duplicados → dedup, asigna una vez
23. Bundle incluye artifact_policy calculada
24. parent_proforma FK en ART-04, ART-09, ART-10 → vinculado correctamente
25. Expediente legacy (pre-S20, sin proformas) → C5 falla con mensaje claro
26. create_proforma mode_b para rana_walk → error (BRAND_ALLOWED_MODES)
27. change_mode rana_walk de default a mode_c → rechazado por BRAND_ALLOWED_MODES (R3-H1)
28. resolve_artifact_policy() brand desconocido CON proformas → fallback REGISTRO genérica, no {}
29. create_proforma con line_ids=null → tratado como lista vacía, no explota (R3-H4)
30. create_proforma con line_ids="string" → error de tipo
31. change_mode marluvas de mode_c a mode_b → void ART-09 si existe (R4-H3, espejo de test 17)
32. create_proforma con line_ids=[True] → error "no acepta booleanos" (R5-H2)
33. create_proforma con line_ids=["1"] → error "solo enteros" (R5-H2)
34. create_proforma para brand desconocida → error "brand no soportada" (R5-H3)
35. change_mode para brand desconocida → error "brand no está configurada" (R6-H2)
```

**Criterio de done:**
- [ ] 35 tests mínimo
- [ ] Todos verdes
- [ ] Tests legacy (pre-S20) siguen verdes (0 regresiones)
- [ ] `python manage.py test` completo verde

---

## Tanda de migraciones

Sprint 20 genera migraciones para 1 app:

```bash
# 1. Verificar estado limpio
python manage.py showmigrations

# 2. Generar migración
python manage.py makemigrations expedientes
# Esperado: AddField(proforma) en EPL + AddField(parent_proforma) en ArtifactInstance

# 3. Verificar — additive only
python manage.py sqlmigrate expedientes XXXX
#    Esperado: ALTER TABLE ADD COLUMN (×2), ambos NULL
#    NO esperado: AlterField, RemoveField, RenameField

# 4. Aplicar
python manage.py migrate

# 5. Verificar
python manage.py check
python manage.py test
```

**Rollback:** Reversible. Ambos campos son nullable. `RemoveField` para cada adición.

---

## Dependencias internas Sprint 20

```
S20-01 (FK proforma en EPL) ──────────┐
S20-02 (FK parent_proforma en AI) ────┤
S20-04 (mode en payload ART-02) ──────┤──→ MIGRACIÓN ÚNICA
                                      │
S20-03 (ART-05 multi-proforma) ───────┤ (depende de S20-02)
                                      │
S20-05 (ArtifactPolicy constante) ────┤ (depende de S20-04)
                                      │
                          ┌───────────┘
                          │
S20-06 (Bundle + policy) ─┤ (depende de S20-05)
S20-07 (C1 flexible) ─────┤ (depende de S20-01)
S20-08 (C5 gate) ─────────┤ (depende de S20-01, S20-04)
S20-09 (Reassign-line) ───┤ (depende de S20-01)
S20-10 (Void por mode) ───┤ (depende de S20-02, S20-04)
S20-11 (Crear proforma) ──┤ (depende de S20-04, S20-05)
                          │
S20-12 (Tests) ────────────┘ (depende de todos)
```

---

## Checklist completa Sprint 20

### Fase 0 — Modelo de datos
- [ ] S20-01: FK proforma nullable en EPL
- [ ] S20-02: FK parent_proforma nullable en ArtifactInstance
- [ ] S20-03: ART-05 acepta linked_proformas en payload
- [ ] S20-04: ART-02 requiere mode en payload

### Fase 1 — ArtifactPolicy engine
- [ ] S20-05: ARTIFACT_POLICY constante + resolve_artifact_policy()
- [ ] S20-06: Bundle retorna artifact_policy calculada

### Fase 2 — C1 + C5
- [ ] S20-07: C1 acepta solo client_id + brand_id
- [ ] S20-08: C5 valida proformas + líneas asignadas + modos

### Fase 3 — Void + proformas + tests
- [ ] S20-09: POST reassign-line/ funcional
- [ ] S20-10: Void automático por cambio de modo
- [ ] S20-11: POST crear proforma con mode y líneas
- [ ] S20-12: 35 tests verdes + 0 regresiones

### CI/CD
- [ ] `python manage.py test` verde
- [ ] `bandit -ll backend/` sin high/critical
- [ ] `npm run lint && npm run typecheck` verde
- [ ] Conventional commits

---

## Excluido explícitamente de Sprint 20

| Feature | Razón | Cuándo |
|---------|-------|--------|
| Frontend de proformas (vista CEO) | Sprint 20B | Después de backend estable |
| Vista portal cliente (OC → líneas) | Sprint 20B | Después de artifact_policy en bundle |
| Eliminar STATE_ARTIFACTS del frontend | Sprint 20B | Depende de artifact_policy en bundle |
| Emails/notificaciones | Sprint 21 | CEO-28 pendiente |
| BrandWorkflowPolicy en DB | Sprint 23 | Cuando haya UI de admin |
| Flujo B completo (portal → ART-01 auto) | Sprint 24 | CEO-26 pendiente |
| Flujo C completo (proforma → email) | Sprint 21 + 20B | Descarga manual primero |

---

## Criterio Sprint 20 DONE

### Obligatorio (bloquea Sprint 20B)
1. FK proforma nullable en EPL funcional
2. FK parent_proforma nullable en ArtifactInstance funcional
3. resolve_artifact_policy() calcula policy correcta por brand × mode
4. Bundle incluye artifact_policy
5. C1 acepta solo client_id + brand_id
6. C5 valida proformas + líneas + modos
7. Crear proforma con mode y asignar líneas → funcional
8. Reassign-line entre proformas → funcional
9. 2 proformas con modos distintos en mismo expediente → funcional
10. Tests verdes (35 mínimo + legacy 0 regresiones)
11. `python manage.py test` verde
12. `bandit -ll backend/` sin high/critical

### Deseable (no bloquea Sprint 20B)
13. Void por cambio de modo completamente funcional
14. ART-05 multi-proforma con validación
15. EventLog estandarizado en todas las operaciones de proforma

---

## Impacto en seguridad

| Superficie | Cambio | Evaluación |
|-----------|--------|------------|
| Bundle detalle | +artifact_policy en respuesta | No expone datos sensibles — solo tipos de artefactos requeridos. Visibility INTERNAL. |
| Reassign-line endpoint | Nuevo endpoint mutante | CEO-only (mismo permiso que merge/split). select_for_update en líneas para evitar race conditions. |
| Crear proforma endpoint | Nuevo endpoint mutante | CEO-only. Validación de propiedad (líneas del mismo expediente). |
| Change-mode endpoint | Nuevo endpoint mutante con void | CEO-only. Requiere confirm_void=true. EventLog registra. |
| C1 flexible | Reduce requerimientos de entrada | No amplía superficie — solo relaja validación de entrada. credit_check sigue ejecutándose. |
| C5 gate | Cambia validaciones | Más restrictivo (ahora requiere proformas + líneas asignadas). No amplía superficie. |

**Conclusión:** Superficie de ataque no se amplía. Los nuevos endpoints son CEO-only con validaciones estrictas. No hay datos CEO-ONLY expuestos.

---

## Lecciones de Sprint 18/19 aplicadas

1. **fk_name en inlines:** Si un modelo tiene múltiples FK al mismo modelo → declarar `fk_name`.
2. **Migración additive-only:** Verificar con `sqlmigrate` antes de aplicar.
3. **CI obligatorio:** bandit + typecheck como criterio DONE, no deseable.
4. **Backward compat como test:** Incluir tests explícitos de "payload viejo sigue funcionando".
5. **EventLog en todo:** Cada operación mutante registra en EventLog (lección S18-18).

---

Stamp: DRAFT v1.6 — Arquitecto (Claude Opus 4.6) — 2026-03-30
