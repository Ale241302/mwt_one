from django.db import models

class QRRoute(models.Model):
    slug = models.CharField(max_length=10, unique=True)
    product_slug = models.CharField(max_length=50)
    product_name = models.CharField(max_length=50)
    destination_template = models.CharField(max_length=500)
    is_active = models.BooleanField(default=True)
    fallback_url = models.URLField(default="https://ranawalk.com")
    override_url = models.URLField(blank=True, null=True)
    override_reason = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.slug} -> {self.product_name}"

class QRScan(models.Model):
    route = models.ForeignKey(
        QRRoute,
        on_delete=models.SET_NULL,
        null=True,
    )
    detected_lang = models.CharField(max_length=2)
    country_code = models.CharField(max_length=2, blank=True)
    user_agent = models.TextField(blank=True)
    ip_hash = models.CharField(max_length=32)
    scanned_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Scan {self.route.slug if self.route else 'Unk'} ({self.detected_lang})"
