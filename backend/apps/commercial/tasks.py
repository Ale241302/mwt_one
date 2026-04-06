"""
S23-07 — Task Celery trimestral: liquidate_rebates()
Mueve ledgers 'accruing' que cumplieron threshold a 'pending_review'.
NUNCA liquida automaticamente.
"""
import logging
from datetime import date

from celery import shared_task
from django.db import transaction

logger = logging.getLogger(__name__)


@shared_task(bind=True, name='apps.commercial.tasks.liquidate_rebates')
def liquidate_rebates(self):
    """
    S23-07: Corre el dia 1 de cada trimestre (1 ene, 1 abr, 1 jul, 1 oct).
    Para cada ledger 'accruing' cuyo period_end < hoy y threshold_met=True,
    lo mueve a 'pending_review'.

    Usa effective threshold: custom del assignment > default del programa.
    NUNCA liquida — solo mueve a pending_review para revision del CEO.
    """
    from apps.commercial.models import RebateLedger, LedgerStatus

    today = date.today()
    logger.info("[liquidate_rebates] Iniciando. Fecha: %s", today)

    candidates = (
        RebateLedger.objects
        .select_related(
            'rebate_assignment__rebate_program',
            'rebate_assignment',
        )
        .filter(
            status=LedgerStatus.ACCRUING,
            period_end__lt=today,
        )
    )

    moved = 0
    skipped = 0

    for ledger in candidates:
        program = ledger.rebate_assignment.rebate_program
        assignment = ledger.rebate_assignment

        threshold_met = _check_effective_threshold(ledger, program, assignment)

        if not threshold_met:
            skipped += 1
            logger.debug(
                "[liquidate_rebates] Ledger %s omitido: threshold no alcanzado.", ledger.id
            )
            continue

        with transaction.atomic():
            locked = (
                RebateLedger.objects
                .select_for_update()
                .filter(id=ledger.id, status=LedgerStatus.ACCRUING)
                .first()
            )
            if locked is None:
                continue

            locked.status = LedgerStatus.PENDING_REVIEW
            locked.save(update_fields=['status', 'updated_at'])
            moved += 1
            logger.info("[liquidate_rebates] Ledger %s -> pending_review.", ledger.id)

    logger.info(
        "[liquidate_rebates] Completado. Movidos: %d | Omitidos (threshold): %d",
        moved, skipped,
    )
    return {'moved': moved, 'skipped': skipped}


def _check_effective_threshold(ledger, program, assignment) -> bool:
    """
    Evalua threshold usando effective values:
    custom del assignment tiene precedencia sobre el programa.
    """
    threshold_type = program.threshold_type

    if threshold_type == 'none':
        return True

    if threshold_type == 'amount':
        effective = (
            assignment.custom_threshold_amount
            if assignment.custom_threshold_amount is not None
            else program.threshold_amount
        )
        if effective is None:
            return False
        return ledger.qualifying_amount >= effective

    if threshold_type == 'units':
        effective = (
            assignment.custom_threshold_units
            if assignment.custom_threshold_units is not None
            else program.threshold_units
        )
        if effective is None:
            return False
        return ledger.qualifying_units >= effective

    return False
