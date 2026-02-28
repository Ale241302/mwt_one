from django.db import models
from django.core.exceptions import ValidationError


class TimestampMixin(models.Model):
    """Mixin that adds created_at and updated_at fields to any model."""
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class AppendOnlyModel(TimestampMixin):
    """
    Base model for ledger-like records (CostLine, PaymentLine).
    Prevents updates and deletes to maintain immutable audit trail.
    """

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        if not self._state.adding:
            raise ValidationError(
                f"{self.__class__.__name__} records are append-only and cannot be updated."
            )
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError(
            f"{self.__class__.__name__} records are append-only and cannot be deleted."
        )
