"""
Sprint 1 — Typed Exceptions
Ref: LOTE_SM_SPRINT1 Item 2, FIX-1 (HTTP status codes)
"""
from rest_framework.exceptions import APIException


class CommandValidationError(APIException):
    """Input invalid or precondition not met → 400 Bad Request."""
    status_code = 400
    default_detail = 'Command validation failed.'
    default_code = 'command_validation_error'


class TransitionNotAllowedError(APIException):
    """Transition is prohibited in the current state → 409 Conflict."""
    status_code = 409
    default_detail = 'State transition not allowed.'
    default_code = 'transition_not_allowed'


class ArtifactMissingError(APIException):
    """Required artifact does not exist → 409 Conflict."""
    status_code = 409
    default_detail = 'Required artifact is missing.'
    default_code = 'artifact_missing'
