import logging

logger = logging.getLogger(__name__)


def parse_marluvas_excel(file) -> tuple:
    """
    Contrato: recibe archivo Excel, retorna (líneas_parseadas, error_log).

    STUB — Fase A: retorna lista vacía + log informativo.
    Fase B reemplaza con mapeo real de columnas cuando CEO proporcione muestra.

    Returns:
        tuple: (list_of_line_dicts, error_message)
    """
    logger.warning(
        "ART-10 Parser: STUB activo — awaiting sample Excel from CEO. "
        "File saved but no lines extracted."
    )
    return [], "Parser not configured - awaiting sample file from CEO (DA-02)"
