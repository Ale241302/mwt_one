"""
S26-04: Email backends abstraction layer.
SendResult enum: SENT / RETRYABLE / PERMANENT — nunca bool.
SMTPBackend: usa Django send_mail (configurado por EMAIL_HOST settings).
SESBackend: usa boto3 SES con retry/permanent mapping.
SandboxedEnvironment: Jinja2 sandbox para templates CEO.
"""
import smtplib
import logging
from abc import ABC, abstractmethod
from enum import Enum

from django.conf import settings
from django.core.mail import send_mail

logger = logging.getLogger(__name__)


class SendResult(Enum):
    SENT = "sent"         # Provider accepted
    RETRYABLE = "retryable"   # Transient error — retry
    PERMANENT = "permanent"   # Bad address, blocked — don't retry


class EmailBackend(ABC):
    @abstractmethod
    def send(self, to: str, subject: str, body: str, from_email: str = None) -> SendResult:
        ...


class SMTPBackend(EmailBackend):
    """
    Backend SMTP via Django's send_mail.
    Mapea excepciones SMTP a SendResult.
    """
    def send(self, to: str, subject: str, body: str, from_email: str = None) -> SendResult:
        from_addr = from_email or settings.DEFAULT_FROM_EMAIL
        try:
            count = send_mail(
                subject=subject,
                message=body,
                from_email=from_addr,
                recipient_list=[to],
                fail_silently=False,
            )
            return SendResult.SENT if count == 1 else SendResult.PERMANENT
        except smtplib.SMTPRecipientsRefused:
            logger.warning(f"[SMTP] Recipients refused: {to}")
            return SendResult.PERMANENT
        except smtplib.SMTPAuthenticationError:
            logger.error("[SMTP] Authentication error — check EMAIL_HOST_USER/PASSWORD")
            return SendResult.RETRYABLE
        except (smtplib.SMTPException, ConnectionError, TimeoutError) as exc:
            logger.warning(f"[SMTP] Transient error: {exc}")
            return SendResult.RETRYABLE


class SESBackend(EmailBackend):
    """
    Backend Amazon SES via boto3.
    Requiere: AWS_SES_REGION, credenciales AWS en env.
    """
    def send(self, to: str, subject: str, body: str, from_email: str = None) -> SendResult:
        try:
            import boto3
            import botocore.exceptions
        except ImportError:
            logger.error("[SES] boto3 not installed. pip install boto3")
            return SendResult.RETRYABLE

        from_addr = from_email or settings.DEFAULT_FROM_EMAIL
        region = getattr(settings, 'AWS_SES_REGION', 'us-east-1')

        try:
            client = boto3.client('ses', region_name=region)
            client.send_email(
                Source=from_addr,
                Destination={'ToAddresses': [to]},
                Message={
                    'Subject': {'Data': subject, 'Charset': 'UTF-8'},
                    'Body': {'Text': {'Data': body, 'Charset': 'UTF-8'}},
                }
            )
            return SendResult.SENT
        except Exception as exc:
            # Importación dinámica de botocore para no fallar si no está instalado
            try:
                import botocore.exceptions
                if hasattr(exc, 'response'):
                    error_code = exc.response.get('Error', {}).get('Code', '')
                    if error_code in ('MessageRejected', 'InvalidParameterValue',
                                      'MailFromDomainNotVerifiedException'):
                        logger.warning(f"[SES] Permanent failure ({error_code}): {to}")
                        return SendResult.PERMANENT
            except Exception:
                pass
            logger.warning(f"[SES] Transient/unknown error: {exc}")
            return SendResult.RETRYABLE


def get_email_backend() -> EmailBackend:
    """Factory — retorna backend configurado via MWT_EMAIL_BACKEND setting."""
    from django.utils.module_loading import import_string
    backend_path = getattr(
        settings,
        'MWT_EMAIL_BACKEND',
        'apps.notifications.backends.SMTPBackend'
    )
    return import_string(backend_path)()
