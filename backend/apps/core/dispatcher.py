# Despachador centralizado para hooks post-comando
# Permite el desacoplamiento de modelos entre aplicaciones.

post_command_hooks = []  # Lista global de hooks registrados

def register_hook(fn):
    """
    Registra una función hook para ser ejecutada después de un comando.
    Evita que aplicaciones secundarias dependan directamente de la aplicación de expedientes.
    """
    if fn not in post_command_hooks:
        post_command_hooks.append(fn)
    return fn
