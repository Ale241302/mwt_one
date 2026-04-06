"""
S23-09 — Management command: seed_artifact_policy
Siembra BrandArtifactPolicyVersion en DB desde la constante ARTIFACT_POLICY de expedientes.
Idempotente: skippea brands que ya tienen una policy activa.
"""
import json
import logging

from django.core.management.base import BaseCommand
from django.db import transaction

logger = logging.getLogger(__name__)

# Constante fuente — definida inline aqui como fallback universal.
# Si en el futuro se mueve a expedientes/artifact_policy.py, importar desde alli.
ARTIFACT_POLICY = {
    "default": {
        "required_artifacts": ["factory_order", "invoice"],
        "optional_artifacts": ["packing_list", "certificate_of_origin"],
        "max_versions": 5,
        "allow_void": True,
    }
}


class Command(BaseCommand):
    help = (
        "S23-09: Siembra BrandArtifactPolicyVersion en DB desde la constante ARTIFACT_POLICY. "
        "Idempotente: skippea brands con policy activa existente."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Muestra que se haria sin persistir nada.',
        )

    def handle(self, *args, **options):
        from apps.brands.models import Brand
        from apps.commercial.models import BrandArtifactPolicyVersion
        from apps.audit.models import ConfigChangeLog, EventLog

        dry_run = options['dry_run']

        try:
            from apps.expedientes.artifact_policy import ARTIFACT_POLICY as SOURCE_POLICY
            policy_data = SOURCE_POLICY
            self.stdout.write("Usando ARTIFACT_POLICY desde apps.expedientes.artifact_policy")
        except ImportError:
            policy_data = ARTIFACT_POLICY
            self.stdout.write("Usando ARTIFACT_POLICY inline (fallback).")

        brands = Brand.objects.all().order_by('id')
        seeded = 0
        skipped = 0

        for brand in brands:
            already_active = BrandArtifactPolicyVersion.objects.filter(
                brand=brand,
                is_active=True,
            ).exists()

            if already_active:
                self.stdout.write(
                    self.style.WARNING(f"  SKIP brand={brand.pk} — ya tiene policy activa.")
                )
                skipped += 1
                continue

            if dry_run:
                self.stdout.write(
                    self.style.SUCCESS(f"  [DRY-RUN] Sembraria policy para brand={brand.pk}.")
                )
                seeded += 1
                continue

            with transaction.atomic():
                last_version = (
                    BrandArtifactPolicyVersion.objects
                    .filter(brand=brand)
                    .order_by('-version')
                    .values_list('version', flat=True)
                    .first()
                )
                next_version = (last_version or 0) + 1

                policy_version = BrandArtifactPolicyVersion.objects.create(
                    brand=brand,
                    version=next_version,
                    artifact_policy=policy_data,
                    is_active=True,
                    notes='Sembrado inicial desde constante Python via seed_artifact_policy.',
                )

                ConfigChangeLog.objects.create(
                    user=None,
                    model_name='BrandArtifactPolicyVersion',
                    record_id=str(policy_version.id),
                    action='create',
                    changes={
                        'new_value': json.dumps(policy_data),
                        'brand_id': str(brand.pk),
                        'version': next_version,
                        'source': 'seed_artifact_policy',
                    },
                )

                EventLog.objects.create(
                    event_type='artifact_policy.seeded',
                    action_source='seed_artifact_policy',
                    actor=None,
                    payload={
                        'brand_id': str(brand.pk),
                        'version': next_version,
                        'policy_version_id': str(policy_version.id),
                    },
                    related_model='BrandArtifactPolicyVersion',
                    related_id=str(policy_version.id),
                )

                seeded += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f"  OK brand={brand.pk} -> v{next_version} creada (id={policy_version.id})."
                    )
                )

        self.stdout.write(
            self.style.SUCCESS(
                f"\nSeed completado. Sembradas: {seeded} | Skipped: {skipped}"
            )
        )
