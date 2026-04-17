class ModuleRegistry:
    """
    Registro central de metadatos de los módulos.
    Mapea nombres de módulos a sus rutas base y clases de servicio.
    """
    
    # Este registro se irá poblando conforme se desacoplen los módulos
    _REGISTRY = {
        'brands': {
            'app_label': 'brands',
            'base_url': '/api/brands/',
            'service_module': 'apps.brands.services',
            'service_class': 'BrandService'
        },
        'productos': {
            'app_label': 'productos',
            'base_url': '/api/productos/',
            'service_module': 'apps.productos.services',
            'service_class': 'ProductService'
        },
        'expedientes': {
            'app_label': 'expedientes',
            'base_url': '/api/expedientes/',
            'service_module': 'apps.expedientes.services',
            'service_class': 'ExpedienteService'
        },
    }
    
    @classmethod
    def get_module_info(cls, module_name):
        return cls._REGISTRY.get(module_name)

    @classmethod
    def get_url(cls, module_name):
        info = cls.get_module_info(module_name)
        return info.get('base_url') if info else None

    @classmethod
    def get_service_path(cls, module_name):
        info = cls.get_module_info(module_name)
        if info:
            return f"{info['service_module']}.{info['service_class']}"
        return None
