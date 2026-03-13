# POL_ARCHIVO — Snapshots de Producción

**Status: PENDIENTE — implementar cuando Paperless-ngx esté activo**

## Reglas (definidas desde ahora)

### Trigger de archivo (se genera PDF inmutable)
- Arte final aprobado para producción
- Listing publicado en marketplace
- Claim aprobado por Compliance
- Contrato o acuerdo firmado (Rogers, proveedores)
- Cambio regulatorio que invalida versión anterior

### Formato
PDF con metadata: fecha, versión, aprobador, entities usadas

### Destino
- Futuro: Paperless-ngx
- Actual: Google Drive

### Regla fundamental
La arquitectura de conocimiento NUNCA guarda snapshots.
Solo guarda datos vivos. El pasado vive en el archivo.

### Agente archivista
Pendiente de crear como servicio de plataforma.
Función: buscar y entregar versiones anteriores. Solo lectura.

---
Stamp: BOOTSTRAP VIGENTE 2026-03-01
Vencimiento: 2026-05-30
Estado: VIGENTE
Aprobador final: CEO
