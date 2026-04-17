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
        'suppliers': {
            'app_label': 'suppliers',
            'base_url': '/api/suppliers/',
            'service_module': 'apps.suppliers.services',
            'service_class': 'SupplierService'
        },
        'nodos': {
            'app_label': 'nodos',
            'base_url': '/api/nodos/',
            'service_module': 'apps.nodos.services',
            'service_class': 'NodeService'
        },
        'clientes': {
            'app_label': 'clientes',
            'base_url': '/api/clientes/',
            'service_module': 'apps.clientes.services',
            'service_class': 'ClientService'
        },
        'inventario': {
            'app_label': 'inventario',
            'base_url': '/api/inventario/',
            'service_module': 'apps.inventario.services',
            'service_class': 'InventoryService'
        },
        'transfers': {
            'app_label': 'transfers',
            'base_url': '/api/transfers/',
            'service_module': 'apps.transfers.services',
            'service_class': 'TransferService'
        },
        'expedientes': {
            'app_label': 'expedientes',
            'base_url': '/api/expedientes/',
            'service_module': 'apps.expedientes.services',
            'service_class': 'ExpedienteService'
        },
        'orders': {
            'app_label': 'orders',
            'base_url': '/api/orders/',
            'service_module': 'apps.orders.services',
            'service_class': 'OrderService'
        },
        'finance': {
            'app_label': 'finance',
            'base_url': '/api/finance/',
            'service_module': 'apps.finance.services',
            'service_class': 'FinanceService'
        },
        'cobros': {
            'app_label': 'cobros',
            'base_url': '/api/cobros/',
            'service_module': 'apps.cobros.services',
            'service_class': 'CobrosService'
        },
        'template': {
            'app_label': 'template',
            'base_url': '/api/template/',
            'service_module': 'apps.template.services',
            'service_class': 'TemplateService'
        },
        'historial': {
            'app_label': 'historial',
            'base_url': '/api/historial/',
            'service_module': 'apps.historial.services',
            'service_class': 'HistorialService'
        },
        'dashboard': {
            'app_label': 'dashboard',
            'base_url': '/api/dashboard/',
            'service_module': 'apps.dashboard.services',
            'service_class': 'DashboardService'
        },
        'portal': {
            'app_label': 'portal',
            'base_url': '/api/portal/',
            'service_module': 'apps.portal.services',
            'service_class': 'PortalService'
        },
    }
    
    @classmethod
    def get_module_info(cls, module_name):
        return cls._REGISTRY.get(module_name)

    @classmethod
    def get_service_path(cls, module_name):
        info = cls.get_module_info(module_name)
        if info:
            return f"{info['service_module']}.{info['service_class']}"
        return None

    @classmethod
    def get_service_class(cls, module_name):
        """Importa y devuelve la clase de servicio para el módulo."""
        path = cls.get_service_path(module_name)
        if not path:
            return None
        
        import importlib
        module_path, class_name = path.rsplit('.', 1)
        try:
            module = importlib.import_module(module_path)
            return getattr(module, class_name)
        except (ImportError, AttributeError):
            return None
    @classmethod
    def get_model(cls, app_label, model_name):
        """Resuelve dinámicamente un modelo de Django para evitar imports circulares."""
        from django.apps import apps
        try:
            return apps.get_model(app_label, model_name)
        except Exception:
            return None
