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


class ReferentialIntegrityService:
    """Servicio para validar integridad referencial en ausencia de ForeignKeys."""
    
    @staticmethod
    def check_exists(module_name, entity_id):
        """Verifica si una entidad existe en el módulo destino."""
        from apps.core.registry import ModuleRegistry
        service_class = ModuleRegistry.get_service_class(module_name)
        if service_class and hasattr(service_class, 'get_entity'):
            return service_class.get_entity(entity_id) is not None
        
        # Fallback: intentar obtener el modelo principal por el nombre del módulo
        try:
            from django.apps import apps
            # Asumimos que el nombre del modelo principal es Capitalize(module_name)
            # o lo buscamos en el registry si se añade allí
            info = ModuleRegistry.get_module_info(module_name)
            if info:
                app_label = info['app_label']
                # Esta es una heurística simple, se puede mejorar
                model_name = module_name.capitalize() if module_name != 'expedientes' else 'Expediente'
                model = apps.get_model(app_label, model_name)
                return model.objects.filter(pk=entity_id, is_active=True).exists()
        except:
            pass
        return False

    @staticmethod
    def validate_reference(module_name, entity_id, field_name="ID"):
        """Valida una referencia y lanza ValidationError si no existe."""
        from django.core.exceptions import ValidationError
        if entity_id and not ReferentialIntegrityService.check_exists(module_name, entity_id):
            raise ValidationError({
                field_name: f"La referencia {entity_id} no existe en el módulo {module_name} o no está activa."
            })
