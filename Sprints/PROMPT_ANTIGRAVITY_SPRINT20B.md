# PROMPT_ANTIGRAVITY_SPRINT20B — Frontend Policy-Driven + Vista Proformas

## TU ROL
Eres AG-03 (frontend developer). Ejecutás el Sprint 20B del proyecto MWT.ONE. Implementás exactamente lo que dice el LOTE_SM_SPRINT20B v1.7. No diseñás, no expandís scope. Si algo no está claro, preguntás al CEO.

## CONTEXTO
Sprint 20B elimina la lógica hardcodeada de artefactos del frontend y la reemplaza por rendering basado en `artifact_policy` del bundle (calculada por backend en Sprint 20). Implementa vista CEO con N proformas y vista portal con OC→líneas.

**Stack:** Next.js 14 App Router, TypeScript strict, CSS variables, Tailwind.

**Dos niveles de policy:**
1. `artifact_policy` del bundle → unión por expediente → para gate de avance
2. `resolveProformaPolicy(brand, mode, state)` → por proforma → para render dentro de cada proforma

## HARD RULES

1. **100% frontend.** 0 cambios backend. 0 migraciones. Si falta endpoint, documentar pendiente.
2. **artifact_policy es SSOT.** Backend dice qué mostrar, frontend renderiza.
3. **0 hex hardcodeados.** CSS variables.
4. **0 `any`.** TypeScript strict. Usar `ArtifactPolicyState`, `ArtifactPolicyMap`, `error: unknown`.
5. **Labels desde ARTIFACT_UI_REGISTRY.** Una sola fuente. No duplicar.
6. **EXPEDIENTE_LEVEL_ARTIFACTS** = ART-01/02/11/12. Se renderizan fuera de proformas.
7. **Gate = pre-check visual.** Backend es validación final. Manejar error 400.
8. **Legacy fallback** con `isLegacyExpediente()` (3 condiciones AND).

## VERIFICACIÓN PREVIA

```bash
# Verificar que S20 expone los campos que necesitamos
grep -n "proforma_id\|parent_proforma" backend/apps/expedientes/serializers.py
grep -n "artifact_policy" backend/apps/expedientes/serializers.py
# Si alguno retorna 0: BLOQUEO — no implementar sin esos campos

# Estado limpio
npm run lint && npm run typecheck
```

## ARCHIVOS A CREAR

```
src/types/expediente.ts                          — ArtifactPolicyState, ArtifactPolicyMap
src/constants/proforma-artifact-policy.ts        — PROFORMA_ARTIFACT_POLICY + EXPEDIENTE_LEVEL_ARTIFACTS
src/constants/artifact-ui-registry.ts            — ARTIFACT_UI_REGISTRY (12 entries)
src/constants/mode-labels.ts                     — MODE_LABELS + MODE_COLORS
src/constants/brand-modes.ts                     — BRAND_ALLOWED_MODES espejo
src/utils/resolve-proforma-policy.ts             — resolveProformaPolicy()
src/utils/legacy-check.ts                        — isLegacyExpediente()
src/components/expedientes/ArtifactSection.tsx    — componente genérico policy-driven
src/components/expedientes/ProformaSection.tsx    — sección de una proforma
src/components/expedientes/ReassignLineModal.tsx  — modal mover líneas
src/components/expedientes/CreateProformaModal.tsx — modal crear proforma
legacy-artifacts.ts                              — constantes viejas como fallback
```

## ITEMS (ver LOTE para detalle completo)

### FASE 0
- S20B-01: Eliminar STATE_ARTIFACTS/ARTIFACT_COMMAND_MAP, consumir bundle
- S20B-02: ArtifactSection genérico (required/optional/gate)
- S20B-03: Artefacto completado = read-only

### FASE 1
- S20B-04: Vista CEO con N proformas (ProformaSection + resolveProformaPolicy)
- S20B-05: Mover líneas entre proformas (ReassignLineModal)
- S20B-06: Gate de avance (pre-check + STATE_TO_ADVANCE_COMMAND + error handling)

### FASE 2
- S20B-07: Vista portal OC→líneas (is_operated_by_mwt condicional)
- S20B-08: Mode labels centralizados
- S20B-09: Modal crear proforma (mode filtrado por brand)
- S20B-10: Solo estado actual + anteriores en DOM

## CHECKLIST PRE-PR

```bash
npm run lint          # verde
npm run typecheck     # verde

# Sanidad
grep -rn "STATE_ARTIFACTS\|ARTIFACT_COMMAND_MAP" frontend/src/ | grep -v legacy  # 0
grep -rn "Orden de Compra\|Proforma MWT" frontend/src/ | grep -v artifact-ui-registry  # 0
grep -rn "#[0-9a-fA-F]\{3,6\}" frontend/src/ | grep -v node_modules | grep -v .css  # 0
grep -rn ": any" frontend/src/components/expedientes/ | grep -v node_modules  # 0
```

## PREGUNTAS PARA EL CEO
Si algo no está cubierto, preguntá. No adivines.
