"""
S10-04b — C22 IssueCommissionInvoice
Domain command + event.
"""
from dataclasses import dataclass, field
from datetime import datetime, UTC
import uuid


@dataclass(frozen=True)
class IssueCommissionInvoice:
    """Command: emit a commission invoice for the expediente."""
    expediente_id: str
    invoice_number: str
    commission_amount: float
    commission_pct: float = 0.0
    notes: str = ""
    issued_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass(frozen=True)
class CommissionInvoiceIssued:
    """Domain event emitted when a commission invoice is created."""
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    expediente_id: str = ""
    invoice_number: str = ""
    commission_amount: float = 0.0
    commission_pct: float = 0.0
    notes: str = ""
    occurred_at: datetime = field(default_factory=lambda: datetime.now(UTC))
