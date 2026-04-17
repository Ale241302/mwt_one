from django.apps import apps

class ModuleService:
    """Servicio base para todos los módulos del sistema distribuido."""
    
    @classmethod
    def get(cls, model_class, entity_id):
        """Obtiene una entidad por ID sin ForeignKey, validando is_active."""
        if entity_id is None:
            return None
        try:
            # Asumimos que todos los modelos nuevos heredan de BaseModel (tienen is_active)
            # Para modelos legacy, fallamos si no tienen is_active o simplemente traemos por pk
            if hasattr(model_class, 'is_active'):
                return model_class.objects.get(pk=entity_id, is_active=True)
            return model_class.objects.get(pk=entity_id)
        except model_class.DoesNotExist:
            return None

    @classmethod
    def get_model(cls, app_label, model_name):
        """Helper para obtener el modelo dinámicamente."""
        return apps.get_model(app_label, model_name)
