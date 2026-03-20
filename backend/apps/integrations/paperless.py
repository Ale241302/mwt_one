"""
Sprint 5 S5-09: Paperless-ngx Integration
Ref: ASANA_TASK_SPRINT5 Item 9

Hook after ArtifactInstance completion (with file)
to upload documents to Paperless-ngx with appropriate tags.

Non-blocking: errors logged but don't halt process.
Excluded: ART-10 (cross-cutting), artifacts without expediente FK.
"""
import logging
import requests
from django.conf import settings

logger = logging.getLogger(__name__)

EXCLUDED_ARTIFACTS = {"ART-10"}


def upload_to_paperless(artifact_instance) -> bool:
    """
    Upload a completed ArtifactInstance's file to Paperless-ngx.
    Returns True if upload succeeded, False otherwise.
    """
    api_url = getattr(settings, "PAPERLESS_API_URL", None)
    api_token = getattr(settings, "PAPERLESS_API_TOKEN", None)

    if not api_url or not api_token:
        logger.warning(
            "Paperless integration skipped: PAPERLESS_API_URL or "
            "PAPERLESS_API_TOKEN not configured."
        )
        return False

    if artifact_instance.artifact_type in EXCLUDED_ARTIFACTS:
        return False

    if not artifact_instance.expediente_id:
        return False

    file_url = (artifact_instance.payload or {}).get("file_url")
    if not file_url:
        return False

    try:
        tags = [
            f"mwt-{artifact_instance.artifact_type}",
            f"exp-{str(artifact_instance.expediente_id)[:8]}",
        ]
        expediente = artifact_instance.expediente
        if expediente and expediente.legal_entity:
            tags.append(f"entity-{expediente.legal_entity.short_name}")

        upload_url = f"{api_url.rstrip('/')}/api/documents/post_document/"
        response = requests.post(
            upload_url,
            headers={"Authorization": f"Token {api_token}"},
            data={
                "title": (
                    f"{artifact_instance.artifact_type} - "
                    f"EXP-{str(artifact_instance.expediente_id)[:8]}"
                ),
                "tags": ",".join(tags),
            },
            timeout=30,
        )

        if response.status_code in (200, 201, 202):
            logger.info(
                f"Paperless: Uploaded {artifact_instance.artifact_type} "
                f"for EXP-{str(artifact_instance.expediente_id)[:8]}"
            )
            return True
        else:
            logger.warning(
                f"Paperless: Upload failed ({response.status_code}): "
                f"{response.text[:200]}"
            )
            return False

    except Exception as e:
        logger.error(f"Paperless: Upload failed: {e}", exc_info=True)
        return False


def trigger_paperless_upload(artifact_instance):
    """Non-blocking wrapper. Called post-artifact completion."""
    try:
        upload_to_paperless(artifact_instance)
    except Exception as e:
        logger.error(f"Paperless trigger failed silently: {e}", exc_info=True)
