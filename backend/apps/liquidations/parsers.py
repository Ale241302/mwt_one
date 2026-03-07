import logging

logger = logging.getLogger(__name__)


def parse_marluvas_liquidation(data: dict) -> list[dict]:
    """
    Parsea el payload JSON del formato MWT InvoiceComisiones DATA.
    Contrato de retorno: lista de dicts listos para crear LiquidationLine.
    """
    lines = []

    for item in data.get("commissions", []):
        lines.append({
            "marluvas_reference":     item.get("fatura", ""),
            "concept":                "comision",
            "client_payment_amount":  item.get("base"),
            "commission_pct_reported": item.get("rate"),
            "commission_amount":      item.get("amount"),
            "currency":               data.get("currency", "USD"),
            "is_partial_payment":     False,   # "Pago total"
            "match_status":           "unmatched",
            "observation":            f"Cliente: {item.get('client', '')}",
        })

    premio = data.get("premio")
    if premio:
        ptax_info = ""
        if premio.get("ptax"):
            ptax_info = f"PTAX {premio.get('ptaxDate', '')} - {premio['ptax']}"
        lines.append({
            "marluvas_reference":     "",
            "concept":                "premio",
            "client_payment_amount":  None,
            "commission_pct_reported": None,
            "commission_amount":      premio.get("amount"),
            "currency":               data.get("currency", "USD"),
            "is_partial_payment":     False,
            "match_status":           "no_match_needed",   # automÃ¡tico per spec
            "observation":            ptax_info or premio.get("label", "Premio de Vendas"),
        })

    logger.info(f"parse_marluvas_liquidation: {len(lines)} lÃ­neas extraÃ­das.")
    return lines
