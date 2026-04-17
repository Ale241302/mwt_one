from apps.core.services import ModuleService
from .models import Node

class NodeService(ModuleService):
    @classmethod
    def get_entity(cls, entity_id):
        return cls.get(Node, entity_id)

    @classmethod
    def get_node_name(cls, node_id):
        node = cls.get_entity(node_id)
        return node.name if node else "Nodo Desconocido"
