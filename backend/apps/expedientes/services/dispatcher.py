# Sprint 18 - T0.5: post_command_hooks en dispatcher
# Importar el dispatcher existente del __init__.py no lo reemplaza;
# este archivo agrega el mecanismo de hooks al dispatch_command existente.

post_command_hooks = []  # Lista modulo-level. Registrar hooks aqui.


def register_hook(fn):
    """Registrar una funcion hook. Sera invocada post-command exitoso."""
    if fn not in post_command_hooks:
        post_command_hooks.append(fn)
    return fn


def dispatch_with_hooks(expediente, command_code, user, handler_fn, **kwargs):
    """
    Ejecuta handler_fn y luego los hooks registrados.
    Los hooks NO se invocan si handler_fn lanza excepcion.
    """
    result = handler_fn(expediente, user, **kwargs)
    for hook in post_command_hooks:
        try:
            hook(
                expediente=expediente,
                command_code=command_code,
                user=user,
                result=result,
            )
        except Exception:
            pass  # hooks no deben romper el flujo principal
    return result
