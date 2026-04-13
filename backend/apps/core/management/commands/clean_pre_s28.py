import logging
from django.core.management.base import BaseCommand
from apps.notifications.models import NotificationTemplate
from apps.brands.models import Brand

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Executes pre-S28 cleanup tasks: removes junk templates, consolidates brands, fixes encoding.'

    def handle(self, *args, **kwargs):
        self.stdout.write("Starting pre-S28 cleanup...")

        self.cleanup_templates()
        self.cleanup_brands()
        self.fix_encoding_issues()

        self.stdout.write(self.style.SUCCESS("S28 cleanup completed successfully."))

    def cleanup_templates(self):
        self.stdout.write("Cleaning up garbage templates...")
        # Soft-delete NotificationTemplates named test or dummy by setting is_active=False
        junk_templates = NotificationTemplate.objects.filter(
            name__icontains='test'
        ) | NotificationTemplate.objects.filter(
            name__icontains='dummy'
        )
        
        count = 0
        for template in junk_templates:
            if template.is_active:
                template.is_active = False
                template.save(update_fields=['is_active'])
                count += 1
                
        self.stdout.write(f"Deactivated {count} garbage templates.")

    def cleanup_brands(self):
        self.stdout.write("Consolidating brand duplicates...")
        brands = Brand.objects.all()
        brand_names = set()
        duplicates = []
        for brand in brands:
            name_lower = brand.name.strip().lower()
            if name_lower in brand_names:
                duplicates.append(brand)
            else:
                brand_names.add(name_lower)
        
        # In deactivate duplicates
        for dup in duplicates:
            if dup.is_active:
                dup.is_active = False
                try:
                    dup.save(update_fields=['is_active'])
                except Exception as e:
                    logger.warning(f"Failed to deactivate brand {dup.slug}: {e}")
                    
        self.stdout.write(f"Processed {len(duplicates)} duplicate brands.")

    def fix_encoding_issues(self):
        self.stdout.write("Fixing encoding issues in models...")
        brands = Brand.objects.all()
        count = 0
        for brand in brands:
            try:
                # Basic encoding fixing pattern
                fixed_name = brand.name.encode('Windows-1252', 'replace').decode('utf-8', 'ignore')
                if fixed_name != brand.name and '' not in fixed_name:
                    brand.name = fixed_name
                    brand.save(update_fields=['name'])
                    count += 1
            except Exception:
                pass
        self.stdout.write(f"Finished fixing encoding issues for {count} records.")
