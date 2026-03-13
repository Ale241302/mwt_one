# POL_STAMP — Contenido Vigente

Ningún output con stamp != VIGENTE sale a producción.

## Estados válidos
- VIGENTE: aprobado y dentro de ciclo 90 días
- VENCIDO: pasó 90 días sin renovación
- EN REVISIÓN: Compliance está evaluando
- OBSERVACIONES COPY: Copy tiene correcciones pendientes
- CORRECCIÓN ENVIADA: Copy devolvió, esperando Compliance

## Formato del stamp
```
Stamp vigente: APROBADO por [nombre] el [YYYY-MM-DD HH:MM]
Vencimiento: [YYYY-MM-DD] (stamp + 90 días)
Estado: [estado]
Aprobador final: [ROL] (actualmente: CEO)
```

---
Stamp: BOOTSTRAP VIGENTE 2026-03-01
Vencimiento: 2026-05-30
Estado: VIGENTE
Aprobador final: CEO
