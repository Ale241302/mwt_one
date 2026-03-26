"""
S17-12: payment_grace_days patch note for ClientSubsidiary.

This file documents the field to be added to ClientSubsidiary.
Run the following migration after applying to clientes/models.py:
    python manage.py makemigrations clientes --name add_payment_grace_days

Field to add to ClientSubsidiary:
    payment_grace_days = models.IntegerField(
        default=15,
        help_text="D\u00edas de gracia post-vencimiento antes de email cobranza."
    )

NOTE: Apply manually to backend/apps/clientes/models.py — this patch file
is documentation only to avoid overwriting existing ClientSubsidiary content
without inspecting the current state of that file first.
"""
# This is a documentation-only file for S17-12
# The actual field must be added to apps/clientes/models.py: ClientSubsidiary
FIELD_DEFINITION = """
    # S17-12: Days of grace after due date before collection email is triggered
    payment_grace_days = models.IntegerField(
        default=15,
        help_text=\"D\u00edas de gracia post-vencimiento antes de email cobranza.\"
    )
"""
