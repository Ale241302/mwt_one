# Sprint 23 — Módulo Commercial

> **Estado:** ✅ Completado y verificado  
> **Fecha de cierre:** 2026-04-06  
> **Branch:** `main`  
> **Rama de feature:** Merges desde `feat/sprint23-fase*` → `main`

---

## Objetivo del Sprint

Crear el módulo `commercial` desde cero: modelos de Rebates, Comisiones y Política de Artefactos; lógica de negocio con servicios y tareas Celery; API REST con permisos por rol; interfaz en el frontend (BrandConsole + Portal); y suite de tests completa.

---

## Fase 0 — Modelos, Migraciones y Resolvers (S23-01 a S23-05)

**Commit:** [`2307841`](https://github.com/Ale241302/mwt_one/commit/2307841555c4d49142d89547d0a08e0178e90c9a)

### Items completados

| ID | Descripción | Estado |
|----|-------------|--------|
| S23-01 | Modelos `RebateProgram` y `RebateProgramProduct` | ✅ |
| S23-02 | Modelos `RebateAssignment`, `RebateLedger` y `RebateAccrualEntry` | ✅ |
| S23-03 | Modelo `CommissionRule` | ✅ |
| S23-04 | Modelo `BrandArtifactPolicyVersion` | ✅ |
| S23-05 | Servicios resolvers (`resolve_rebate`, `resolve_commission`, `resolve_artifact_policy`) | ✅ |

### Archivos creados

```
backend/apps/commercial/__init__.py
backend/apps/commercial/apps.py
backend/apps/commercial/models.py
backend/apps/commercial/services/__init__.py
backend/apps/commercial/services/rebate_resolver.py
backend/apps/commercial/services/commission_resolver.py
backend/apps/commercial/services/artifact_policy_resolver.py
backend/apps/commercial/migrations/0001_initial.py
backend/apps/commercial/migrations/0002_rebateaccrualentry_rebate_ledger.py
backend/apps/commercial/migrations/0003_alter_commissionrule.py
backend/apps/commercial/migrations/0004_brandartifactpolicyversion.py
```

### Archivos modificados

```
backend/config/settings/base.py          — agregar apps.commercial a INSTALLED_APPS
```

### Solución

- Se definió la app `commercial` con todos sus modelos en `models.py`.
- Se crearon 4 migraciones iniciales cubriendo la creación de todas las tablas.
- Los resolvers siguen el patrón de servicio puro (sin side-effects), retornando el objeto de configuración aplicable según jerarquía brand → client → subsidiary → default.
- **Fix posterior:** `apps.commercial` no estaba en `INSTALLED_APPS`, causando que Django levantara con 500 en todos los endpoints. Se agregó en [`d9cff50`](https://github.com/Ale241302/mwt_one/commit/d9cff507d958ab3f76e37fe1737bee9f32be3317).

---

## Fase 1 — Business Logic Layer (S23-06 a S23-09)

**Commit:** [`c577793`](https://github.com/Ale241302/mwt_one/commit/c5777932a1418c6552395a8aa8b768d678d0e446)

### Items completados

| ID | Descripción | Estado |
|----|-------------|--------|
| S23-06 | Modelo `EventLog` + migración en `apps.audit` | ✅ |
| S23-07 | Función `calculate_rebate_accrual` — cálculo de devengamiento por pedido | ✅ |
| S23-07b | Tarea Celery `liquidate_rebates` — schedule trimestral automático | ✅ |
| S23-08 | Función `approve_rebate_liquidation` — aprobación CEO con registro en ledger | ✅ |
| S23-09 | Management command `seed_artifact_policy` — datos semilla de política de artefactos | ✅ |

### Archivos creados

```
backend/apps/commercial/tasks.py
backend/apps/commercial/services/rebate_service.py
backend/apps/commercial/management/__init__.py
backend/apps/commercial/management/commands/__init__.py
backend/apps/commercial/management/commands/seed_artifact_policy.py
backend/apps/audit/models.py                          — modelo EventLog
backend/apps/audit/migrations/0001_eventlog.py
```

### Archivos modificados

```
backend/config/celery.py                              — agregar beat schedule trimestral
```

### Solución

- `calculate_rebate_accrual` recibe un `factory_order` y calcula el monto de rebate según el programa activo para la marca/cliente, acumulando en `RebateAccrualEntry`.
- `liquidate_rebates` es una tarea Celery que corre el último día del trimestre, agrega las entradas pendientes y crea el `RebateLedger` con estado `pending_approval`.
- `approve_rebate_liquidation` permite al CEO aprobar una liquidación, cambia el estado a `liquidated` y registra el evento en `EventLog`.
- **Fix posterior:** `RebateLedger.liquidated_by` apuntaba a `users.User` en lugar de `users.MWTUser` causando error de migración. Corregido en [`611020b`](https://github.com/Ale241302/mwt_one/commit/611020bb27f07c37f5fc2d18116b3de02a752ac2). También se corrigió `CharField max_digits → max_length` en `liquidation_type` en [`8efb935`](https://github.com/Ale241302/mwt_one/commit/8efb935a871798cee65c260097d1b1957b1bb52f).
- **Fix posterior:** `related_name` en `audit.EventLog.actor` colisionaba con `expedientes.EventLog.user`. Renombrado en [`bbf22c0`](https://github.com/Ale241302/mwt_one/commit/bbf22c032dd2e6f67a8a47140255c4db3830fcca).

---

## Fase 2 — API REST (S23-10 a S23-12)

**Commit:** [`cbdfb46`](https://github.com/Ale241302/mwt_one/commit/cbdfb461403bb078a869cc7216254471d2838365)

### Items completados

| ID | Descripción | Estado |
|----|-------------|--------|
| S23-10 | API Rebates: `RebateProgramViewSet`, `RebateLedgerViewSet`, `RebateAccrualEntryViewSet` | ✅ |
| S23-11 | API Comisiones: `CommissionRuleViewSet` — CRUD restringido a CEO | ✅ |
| S23-12 | API ArtifactPolicy: `BrandArtifactPolicyVersionViewSet` — lectura por representante | ✅ |

### Archivos creados

```
backend/apps/commercial/permissions.py
backend/apps/commercial/serializers.py
backend/apps/commercial/views.py
backend/apps/commercial/urls.py
```

### Archivos modificados

```
backend/config/urls.py                                — incluir commercial.urls bajo /api/commercial/
```

### Solución

- Se crearon permisos granulares en `permissions.py`: `IsCEO`, `IsRepresentative`, `IsCEOOrReadOnly`.
- Los `ViewSets` aplican permisos por acción (`get_permissions` override).
- `RebateLedgerViewSet` expone acción extra `@action(detail=True, methods=['post']) approve` accesible solo a CEO.
- `BrandArtifactPolicyVersionViewSet` es read-only para representantes, write para CEO.

---

## Fase 3 — Frontend (S23-13 a S23-15)

**Commit principal:** [`cfba5bf`](https://github.com/Ale241302/mwt_one/commit/cfba5bfe3055cda56cf09f82e8b6124e700e7826)  
**Merge PR #59:** [`45d3d1e`](https://github.com/Ale241302/mwt_one/commit/45d3d1e87e4eda732707422315e7736ba1c4d441)

### Items completados

| ID | Descripción | Estado |
|----|-------------|--------|
| S23-13 | Componente `CommissionsSection` — CRUD de reglas de comisión (solo CEO) | ✅ |
| S23-14 | Componente `RebatesSection` — CRUD de programas de rebate | ✅ |
| S23-14b | Componente `ArtifactPolicySection` — visualización de política de artefactos por marca | ✅ |
| S23-15 | Tab `Commercial` en `BrandConsole` y en `Portal` | ✅ |

### Archivos creados

```
frontend/src/components/commercial/CommissionsSection.tsx
frontend/src/components/commercial/RebatesSection.tsx
frontend/src/components/commercial/ArtifactPolicySection.tsx
frontend/src/components/commercial/CommercialTab.tsx
```

### Archivos modificados

```
frontend/src/app/[locale]/brands/[brandId]/page.tsx   — agregar tab Commercial a BrandConsole
frontend/src/app/[locale]/portal/page.tsx             — agregar tab Commercial a Portal
frontend/src/components/brands/tabs/CatalogTab.tsx    — brandId opcional para desbloquear build
frontend/src/components/brands/tabs/PricingTab.tsx    — brandId opcional
frontend/src/components/brands/tabs/AssignmentsTab.tsx — brandId opcional
frontend/src/components/brands/tabs/PaymentTermsTab.tsx — brandId opcional
```

### Solución

- `CommercialTab` actúa como orquestador: renderiza `RebatesSection`, `CommissionsSection` (solo si `user.role === 'CEO'`) y `ArtifactPolicySection`.
- `ArtifactPolicySection` escapa comillas en JSX para pasar el build de ESLint (fix [`c7ac1e4`](https://github.com/Ale241302/mwt_one/commit/c7ac1e45b9c047e9673623d24f35981c21925689)).
- Los props `brandId` se hicieron opcionales en los tabs existentes para no bloquear el build mientras el contexto de página aún no los provee (fix [`aaff95f`](https://github.com/Ale241302/mwt_one/commit/aaff95fefd880ba35f621ae659f552647c53a144), [`9cca822`](https://github.com/Ale241302/mwt_one/commit/9cca822d8e089a775d35494ad91a5399e52cc686)).

---

## Fase 4 — Suite de Tests (S23-16)

**Commit principal:** [`88313e8`](https://github.com/Ale241302/mwt_one/commit/88313e8228768e6d4281c827b6dd1952132f0316)  
**Merge PR #60:** [`e45aaa4`](https://github.com/Ale241302/mwt_one/commit/e45aaa4d6e7660d367aac0b0648df31e9ee9ceb0)

### Items completados

| ID | Grupo | Tests | Estado |
|----|-------|-------|---------|
| T1 | `RebateProgram` CRUD | 4 | ✅ |
| T2 | `RebateProgramProduct` | 4 | ✅ |
| T3 | `RebateAssignment` | 4 | ✅ |
| T4 | `RebateLedger` | 4 | ✅ |
| T5 | `RebateAccrualEntry` | 4 | ✅ |
| T6 | `calculate_rebate_accrual` service | 4 | ✅ |
| T7 | `approve_rebate_liquidation` service | 4 | ✅ |
| T8 | `liquidate_rebates` Celery task | 4 | ✅ |
| T9 | `CommissionRule` CRUD + permisos CEO | 4 | ✅ |
| T10 | `resolve_commission` resolver | 4 | ✅ |
| T11 | `BrandArtifactPolicyVersion` API | 4 | ✅ |
| T12 | `EventLog` registro de acciones | 4 | ✅ |
| T13 | Permisos de acceso por rol | 4 | ✅ |
| T14 | Integración end-to-end: accrual → liquidation → approval | 4 | ✅ |
| **Total** | | **56 tests** | **✅** |

### Archivos creados

```
backend/apps/commercial/tests/__init__.py
backend/apps/commercial/tests/test_rebate_program.py
backend/apps/commercial/tests/test_rebate_program_product.py
backend/apps/commercial/tests/test_rebate_assignment.py
backend/apps/commercial/tests/test_rebate_ledger.py
backend/apps/commercial/tests/test_rebate_accrual_entry.py
backend/apps/commercial/tests/test_calculate_rebate_accrual.py
backend/apps/commercial/tests/test_approve_rebate_liquidation.py
backend/apps/commercial/tests/test_liquidate_rebates_task.py
backend/apps/commercial/tests/test_commission_rule.py
backend/apps/commercial/tests/test_permissions.py
```

---

## Fase 5 — Hotfixes Post-Merge (Día del Sprint)

Hotfixes aplicados directamente en `main` tras detectar errores en producción/build.

| Commit | Descripción | Archivo afectado |
|--------|-------------|------------------|
| [`d9cff50`](https://github.com/Ale241302/mwt_one/commit/d9cff507d958ab3f76e37fe1737bee9f32be3317) | `apps.commercial` no estaba en `INSTALLED_APPS` → Django 500 en todos los endpoints | `backend/config/settings/base.py` |
| [`611020b`](https://github.com/Ale241302/mwt_one/commit/611020bb27f07c37f5fc2d18116b3de02a752ac2) | `RebateLedger.liquidated_by` apuntaba a `users.User` en lugar de `users.MWTUser` | `backend/apps/commercial/models.py` |
| [`8efb935`](https://github.com/Ale241302/mwt_one/commit/8efb935a871798cee65c260097d1b1957b1bb52f) | `CharField` con `max_digits` en lugar de `max_length` en `liquidation_type` | `backend/apps/commercial/models.py` |
| [`bbf22c0`](https://github.com/Ale241302/mwt_one/commit/bbf22c032dd2e6f67a8a47140255c4db3830fcca) | `related_name` clash entre `audit.EventLog.actor` y `expedientes.EventLog.user` | `backend/apps/audit/models.py` |
| [`c49924a`](https://github.com/Ale241302/mwt_one/commit/c49924aff67e16f752b73bffb1def4d68a5b7aa2) | Migración `0002` reescrita para coincidir con `models.py` actual | `backend/apps/commercial/migrations/0002_*.py` |
| [`71077531`](https://github.com/Ale241302/mwt_one/commit/71077531615176b969139dc92e3bbf277faa659c) | FK `rebate_ledger` faltante en `RebateAccrualEntry` + `unique_together` incorrecto | `backend/apps/commercial/models.py` |
| [`a2d7ab1`](https://github.com/Ale241302/mwt_one/commit/a2d7ab10b10dbd1678504f15d1e40f1d38db6633) | Migración `0005` — refactor completo de tablas y campos para alinear con modelos finales | `backend/apps/commercial/migrations/0005_*.py` |
| [`5b83bf4`](https://github.com/Ale241302/mwt_one/commit/5b83bf44f248bb3b0c5ffcda39e7875b70ab5c46) | `AlterModelTable` con `model_name=` en lugar de `name=` | `backend/apps/commercial/migrations/0005_*.py` |
| [`96e993f`](https://github.com/Ale241302/mwt_one/commit/96e993f99ab015afa249d6ab0578a02550306bec) | Args posicionales incorrectos en operaciones de migración 0005 | `backend/apps/commercial/migrations/0005_*.py` |
| [`419cfdb`](https://github.com/Ale241302/mwt_one/commit/419cfdb2792c073800a84c771af87d37143a3e2b) | `ClientSubsidiary.payment_grace_days` movido a migración de app `clientes` | `backend/apps/clientes/migrations/` |
| [`21047e7`](https://github.com/Ale241302/mwt_one/commit/21047e7acad5fb1fc8d0d48a2b3cf1b1f8e09d75) | Campos incorrectos de `BrandSKU` en `catalog` view (pricing) | `backend/apps/pricing/views.py` |
| [`5f68b57`](https://github.com/Ale241302/mwt_one/commit/5f68b57fb54bee18027e9a14a2e5013a145cefa4) | Form Rebates: choices inválidos en `period_type`, input brand → select, unificar `threshold_value` | `frontend/src/components/commercial/RebatesSection.tsx` |
| [`0334f46`](https://github.com/Ale241302/mwt_one/commit/0334f462c3e4917910452ddcb53ecb4297a61edb) | Form Comisiones: input brand UUID → select cargado desde `/brands/`; reset scope_id al cambiar scope | `frontend/src/components/commercial/CommissionsSection.tsx` |

---

## Fase 6 — Auditoría de Seguridad (AUDIT_GITHUB_COWORK_2026-04-06)

**Commit:** [`b46f55e`](https://github.com/Ale241302/mwt_one/commit/b46f55e9c18f354f92b903ac998c1f8870b36d7c)

| ID | Hallazgo | Acción | Estado |
|----|----------|--------|--------|
| HAL-01 | Passwords hardcodeadas en `docker-compose.yml` (Redis, Paperless) | Movidas a variables de entorno | ✅ |
| HAL-02 | Archivos de logs con datos reales en el repositorio (`mwt_logs.txt`, `out.txt`, etc.) | Eliminados + `.gitignore` actualizado | ✅ |
| HAL-03 | Seed data con nombres reales de clientes y montos reales | Anonimizados en los 3 scripts `seed_demo_data.py` | ✅ |
| HAL-04 | `SECRET_KEY` con valor por defecto en `settings/base.py` + `OPENAI_API_KEY` en docs | Eliminado default; sanitizados docs de sprint | ✅ |

### Archivos modificados

```
docker-compose.yml
backend/config/settings/base.py
backend/apps/*/management/commands/seed_demo_data.py  (x3)
.gitignore
```

### Archivos eliminados

```
mwt_logs.txt
logs_django.txt
out.txt
salida.txt
```

---

## Resumen de archivos del Sprint

### Backend — Creados (32 archivos)

```
backend/apps/commercial/__init__.py
backend/apps/commercial/apps.py
backend/apps/commercial/models.py
backend/apps/commercial/permissions.py
backend/apps/commercial/serializers.py
backend/apps/commercial/views.py
backend/apps/commercial/urls.py
backend/apps/commercial/tasks.py
backend/apps/commercial/services/__init__.py
backend/apps/commercial/services/rebate_resolver.py
backend/apps/commercial/services/commission_resolver.py
backend/apps/commercial/services/artifact_policy_resolver.py
backend/apps/commercial/services/rebate_service.py
backend/apps/commercial/management/__init__.py
backend/apps/commercial/management/commands/__init__.py
backend/apps/commercial/management/commands/seed_artifact_policy.py
backend/apps/commercial/migrations/__init__.py
backend/apps/commercial/migrations/0001_initial.py
backend/apps/commercial/migrations/0002_rebateaccrualentry_rebate_ledger.py
backend/apps/commercial/migrations/0003_alter_commissionrule.py
backend/apps/commercial/migrations/0004_brandartifactpolicyversion.py
backend/apps/commercial/migrations/0005_sprint23_refactor.py
backend/apps/commercial/tests/__init__.py
backend/apps/commercial/tests/test_rebate_program.py
backend/apps/commercial/tests/test_rebate_program_product.py
backend/apps/commercial/tests/test_rebate_assignment.py
backend/apps/commercial/tests/test_rebate_ledger.py
backend/apps/commercial/tests/test_rebate_accrual_entry.py
backend/apps/commercial/tests/test_calculate_rebate_accrual.py
backend/apps/commercial/tests/test_approve_rebate_liquidation.py
backend/apps/commercial/tests/test_liquidate_rebates_task.py
backend/apps/commercial/tests/test_commission_rule.py
backend/apps/commercial/tests/test_permissions.py
backend/apps/audit/models.py
backend/apps/audit/migrations/0001_eventlog.py
```

### Backend — Modificados

```
backend/config/settings/base.py
backend/config/urls.py
backend/config/celery.py
backend/apps/pricing/views.py
backend/apps/clientes/migrations/  (nueva migración payment_grace_days)
backend/apps/audit/models.py       (related_name fix)
docker-compose.yml
.gitignore
```

### Frontend — Creados (4 archivos)

```
frontend/src/components/commercial/CommissionsSection.tsx
frontend/src/components/commercial/RebatesSection.tsx
frontend/src/components/commercial/ArtifactPolicySection.tsx
frontend/src/components/commercial/CommercialTab.tsx
```

### Frontend — Modificados

```
frontend/src/app/[locale]/brands/[brandId]/page.tsx
frontend/src/app/[locale]/portal/page.tsx
frontend/src/components/brands/tabs/CatalogTab.tsx
frontend/src/components/brands/tabs/PricingTab.tsx
frontend/src/components/brands/tabs/AssignmentsTab.tsx
frontend/src/components/brands/tabs/PaymentTermsTab.tsx
```

---

## Conteo final

| Categoría | Cantidad |
|-----------|----------|
| Items del sprint completados | 16 (S23-01 a S23-16) |
| Hotfixes aplicados | 13 |
| Archivos creados (backend) | 35 |
| Archivos creados (frontend) | 4 |
| Archivos modificados | 15 |
| Tests escritos | 56 (14 grupos × 4) |
| Hallazgos de seguridad resueltos | 4 (HAL-01 a HAL-04) |
| PRs mergeadas | 2 (#59 Fase 3, #60 Fase 4) |
| Estado general | ✅ Sin pendientes |
