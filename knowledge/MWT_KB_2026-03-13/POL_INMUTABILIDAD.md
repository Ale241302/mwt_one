# POL_INMUTABILIDAD — No Se Recalcula el Pasado

Precios, comisiones y atribuciones registradas son inmutables.

## Regla
- PriceTable: una vez effective, el precio histórico no se modifica. Nueva versión = nuevo registro con effective_from.
- Attribution Ledger: eventos append-only. No se editan ni eliminan.
- Payouts: una vez PAYOUT_APPROVED, el monto no cambia. Correcciones = nuevo evento.
- Expedientes: costos registrados en un expediente cerrado no se recalculan.

## Alcance
Aplica a: pricing/, affiliates/, payments/, expedientes/

## Justificación
Recalcular el pasado corrompe auditorías, reportes financieros y confianza del sistema. Si hay error, se corrige hacia adelante con nuevo registro documentado.

---
Stamp: BOOTSTRAP VIGENTE 2026-03-01
Vencimiento: 2026-05-30
Estado: VIGENTE
Aprobador final: CEO
