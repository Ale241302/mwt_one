import re

with open('/app/apps/expedientes/models.py', 'r') as f:
    content = f.read()

old = "        default=CreditClockStartRule.ON_CREATION)"
new = """        default=CreditClockStartRule.ON_CREATION)
    credit_clock_started_at = models.DateTimeField(
        blank=True, null=True, default=None,
        help_text='Timestamp when credit clock started (FIX-7)')"""

content = content.replace(old, new)

with open('/app/apps/expedientes/models.py', 'w') as f:
    f.write(content)

print('credit_clock_started_at field added successfully')
