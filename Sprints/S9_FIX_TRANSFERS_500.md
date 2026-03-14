# S9-11 — Fix /api/transfers/ — Error 500

Branch: `fix/s9-transfers-500`
Item: S9-11
Agente: AG-02 Backend
Prioridad: P1 (Bloqueador para S9-12)
**Estado:** ⏳ PENDIENTE

---

## Problema

`GET /api/transfers/` retorna HTTP 500.

## Posibles causas

1. **Serializer con campo inexistente** — el serializer de Transfer referencia un campo que fue renombrado o eliminado en el modelo.
2. **FK rota** — una ForeignKey apunta a un modelo que no existe o fue movido.
3. **Migración pendiente** — hay un campo en el modelo que no está reflejado en la DB.
4. **Import error** — algún import en views.py o serializers.py falla silenciosamente.

## Pasos de debug

1. Revisar logs del servidor cuando se hace `GET /api/transfers/`:
   ```bash
   docker-compose logs backend | grep -i error | tail -50
   ```

2. Ejecutar en Django shell:
   ```python
   from logistics.models import Transfer  # ajustar import según estructura
   Transfer.objects.all()[:5]
   ```

3. Verificar serializer:
   ```python
   from logistics.serializers import TransferSerializer  # ajustar
   t = Transfer.objects.first()
   if t:
       s = TransferSerializer(t)
       print(s.data)
   ```

4. Verificar migraciones pendientes:
   ```bash
   python manage.py showmigrations | grep -v '[X]'
   python manage.py migrate --check
   ```

## Criterio DONE

- [ ] `GET /api/transfers/` retorna HTTP 200
- [ ] Respuesta es una lista (puede estar vacía)
- [ ] Sin errores en logs del servidor
- [ ] `GET /api/transfers/{id}/` también retorna 200 o 404 (nunca 500)

## Impacto

Este fix es **bloqueador** para S9-12 (UI de Transfers). No construir frontend hasta que este endpoint esté limpio.

---

*Spec: LOTE_SM_SPRINT9.md v2.0 | Sprint 9 Fase 3*
