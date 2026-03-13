# POL_ITERACION — Flujo de Trabajo Agente

## Fase 1: Conversar
Iterar decisiones en texto puro contra la taxonomía. Sin crear archivos. Acumular resoluciones.

## Fase 2: Indexar
Cuando CEO dice "indexá":
1. Ejecutar checks de taxonomía antes de entregar (refs válidas, policies aplicadas, campos completos, POL_VACIO, POL_NUNCA_TRADUCIR, POL_ANTI_CONFUSION, POL_DETERMINISMO)
2. Si algo se sale de la taxonomía → explicar al CEO qué y por qué
3. Si algo es ambiguo entre dos clasificaciones → el agente decide y resuelve. No pregunta, actúa como experto.
4. Si algún archivo del proyecto debe eliminarse (superseded, duplicado, renombrado) → informar al CEO explícitamente antes de entregar
5. Reportar resultado del check
6. Presentar cada archivo individual listo para incorporar al proyecto
7. Si CEO pide ZIP → se hace ZIP

## Regla
- Nunca crear archivos intermedios que se van a reconstruir
- Decisión no cerrada = no se materializa
- El agente es el experto en la taxonomía. Busca, encuentra, clasifica y resuelve.
- Archivo que debe eliminarse del proyecto = informar siempre. Nunca asumir que el CEO lo sabe.

---
Stamp: BOOTSTRAP VIGENTE 2026-03-01
Vencimiento: 2026-05-30
Estado: VIGENTE
Aprobador final: CEO
