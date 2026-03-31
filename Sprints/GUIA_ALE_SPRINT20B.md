# GUIA_ALE_SPRINT20B — Sprint 20B: Frontend Policy-Driven + Vista Proformas

**Sprint 20 backend DONE** (35/35 tests, 0 regresiones). Todos los endpoints y el bundle con `artifact_policy` están listos. Podés arrancar S20B.

Ale, este sprint cambia cómo el frontend decide qué artefactos mostrar. Hasta ahora el frontend decidía con constantes hardcodeadas (`STATE_ARTIFACTS`). A partir de Sprint 20B, el frontend **NO decide** — lee `artifact_policy` del bundle y renderiza lo que el backend dice.

**Antes de arrancar, verificá que el serializer expone los campos nuevos:**
```bash
grep -n "proforma" backend/apps/expedientes/serializers.py
grep -n "parent_proforma" backend/apps/expedientes/serializers.py
```
Si alguno no aparece como campo del serializer, agregalo (2 líneas) antes de empezar.

---

## El cambio en una frase

**Antes:** Frontend decide qué artefactos mostrar por estado (hardcoded)
**Después:** Backend calcula, frontend solo renderiza

---

## Dos niveles de policy (importante)

1. **`artifact_policy` del bundle** — unión de todas las proformas. Se usa para el **gate de avance** a nivel expediente (botón "Avanzar").
2. **`resolveProformaPolicy(brand, mode, state)`** — policy específica de CADA proforma. Se usa para renderizar artefactos **dentro** de cada proforma.

Son dos cosas distintas. No confundir.

---

## Qué vas a construir (en orden)

### Fase 0 — Limpiar hardcoded + componente genérico

1. **Eliminar STATE_ARTIFACTS, ARTIFACT_COMMAND_MAP** de `ExpedienteAccordion.tsx`. Mover a `legacy-artifacts.ts` como fallback para expedientes viejos.

2. **Crear `ArtifactSection.tsx`** — componente genérico que recibe policy de un estado y renderiza: required siempre visible, optional como botón "+ Agregar", gate como indicador de bloqueo.

3. **Artefacto completado = read-only.** Badge "Completado ✓". No hay botón editar.

### Fase 1 — Vista CEO con proformas

4. **`ProformaSection.tsx`** — cada proforma como sección con badge de mode (Comisión/FULL/Estándar), líneas, y artefactos hijos. Usa `resolveProformaPolicy()` para saber qué artefactos mostrar.

5. **Mover líneas** entre proformas con modal + endpoint `reassign-line/`. Solo en REGISTRO.

6. **Gate de avance** — pre-check visual. Si faltan artefactos del gate → botón deshabilitado + tooltip. Si backend rechaza → mostrar error.

### Fase 2 — Portal + cleanup

7. **Vista portal** — OC → líneas con estado. 0 proformas/modos/costos visibles. Señal "Operado por Muito Work" solo si el endpoint retorna `is_operated_by_mwt`.

8. **Mode labels centralizados** en `mode-labels.ts` (MODE_LABELS + MODE_COLORS).

9. **Modal crear proforma** con mode filtrado por brand.

10. **Solo estado actual + anteriores** en el acordeón. Futuros NO se renderizan.

---

## Archivos nuevos que vas a crear

| Archivo | Qué hace |
|---------|----------|
| `src/components/expedientes/ArtifactSection.tsx` | Componente genérico policy-driven |
| `src/components/expedientes/ProformaSection.tsx` | Sección de una proforma |
| `src/components/expedientes/ReassignLineModal.tsx` | Modal mover líneas |
| `src/components/expedientes/CreateProformaModal.tsx` | Modal crear proforma |
| `src/constants/proforma-artifact-policy.ts` | PROFORMA_ARTIFACT_POLICY espejo + EXPEDIENTE_LEVEL_ARTIFACTS |
| `src/constants/artifact-ui-registry.ts` | Label + modal + handler por artifact_type |
| `src/constants/mode-labels.ts` | MODE_LABELS + MODE_COLORS |
| `src/constants/brand-modes.ts` | BRAND_ALLOWED_MODES espejo backend |
| `src/utils/resolve-proforma-policy.ts` | Función resolveProformaPolicy() |
| `src/utils/legacy-check.ts` | isLegacyExpediente() helper |
| `src/types/expediente.ts` | ArtifactPolicyState + ArtifactPolicyMap |
| `src/app/.../expedientes/[id]/legacy-artifacts.ts` | Constantes viejas como fallback |

## Archivos que vas a modificar

| Archivo | Qué cambiar |
|---------|-------------|
| `ExpedienteAccordion.tsx` | Eliminar STATE_ARTIFACTS/ARTIFACT_COMMAND_MAP, consumir policy del bundle |
| `ArtifactModal.tsx` | Read-only para status=COMPLETED |
| Detalle expediente page | Agregar ProformaSection, gate UI |
| Portal page | Tabla OC→líneas con estado |

## Archivos que NO podés tocar

- Nada en `backend/` — este sprint es 100% frontend
- `docker-compose.yml`

---

## Reglas clave

1. **artifact_policy del bundle es SSOT** para saber qué artefactos existen. Si no viene, no se muestra.
2. **PROFORMA_ARTIFACT_POLICY** es espejo del backend. Si el backend cambia, este archivo se actualiza.
3. **EXPEDIENTE_LEVEL_ARTIFACTS** = ART-01, ART-02, ART-11, ART-12. Se renderizan a nivel expediente, NO dentro de proformas.
4. **Labels de artefactos** → `ARTIFACT_UI_REGISTRY[type].label`. Una sola fuente.
5. **Mode labels** → `MODE_LABELS` en `mode-labels.ts`.
6. **Gate es pre-check visual** — el backend sigue siendo la validación final. Manejar error 400.
7. **0 hex hardcodeados** — todo CSS variables.
8. **0 `any`** en TypeScript. Usar `ArtifactPolicyState`, `ArtifactPolicyMap`, `unknown` con narrow.
9. **Legacy fallback** — expedientes sin proformas en estados > REGISTRO usan `isLegacyExpediente()` y se renderizan con lógica anterior.

---

## Contrato del bundle (qué consumís)

```typescript
// GET /api/ui/expedientes/{id}/ retorna:
data.artifact_policy          // ArtifactPolicyMap — para gate
data.product_lines[].proforma_id  // para agrupar por proforma
data.artifacts[].parent_proforma_id  // para filtrar hijos por proforma
data.artifacts[].artifact_type     // "ART-01", etc.
data.artifacts[].status            // "COMPLETED", "DRAFT", "VOIDED"
data.artifacts[].payload.mode      // en ART-02
data.brand.slug                    // para resolver policy
```

**Verificación antes de implementar:**
```bash
grep -n "proforma_id\|parent_proforma" backend/apps/expedientes/serializers.py
# Si retorna 0: BLOQUEO de S20 — no implementar S20B-04/05/07 hasta que se resuelva
```

---

## Verificación antes de hacer PR

```bash
npm run lint        # verde
npm run typecheck   # verde

# Sanidad
grep -rn "STATE_ARTIFACTS\|ARTIFACT_COMMAND_MAP" frontend/src/ | grep -v legacy  # 0
grep -rn "Orden de Compra\|Proforma MWT" frontend/src/ | grep -v artifact-ui-registry  # 0
grep -rn "#[0-9a-fA-F]\{3,6\}" frontend/src/ | grep -v node_modules | grep -v .css  # 0 hex
```

---

## Si tenés dudas

- Sobre qué artefactos mostrar: lee DIRECTRIZ_ARTEFACTOS_MODULARES
- Sobre la state machine: lee ENT_OPS_STATE_MACHINE (FROZEN)
- Sobre la policy espejo: lee `PROFORMA_ARTIFACT_POLICY` en `constants/proforma-artifact-policy.ts`
- Sobre algo no cubierto: preguntale al CEO
