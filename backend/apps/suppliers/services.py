from apps.core.services import ModuleService
from .models import Supplier

class SupplierService(ModuleService):
    @classmethod
    def get_entity(cls, entity_id):
        return cls.get(Supplier, entity_id)

    @classmethod
    def get_supplier_name(cls, supplier_id):
        supplier = cls.get_entity(supplier_id)
        return supplier.name if supplier else "Proveedor Desconocido"
