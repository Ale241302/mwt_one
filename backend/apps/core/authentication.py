"""
apps/core/authentication.py

CsrfExemptSessionAuthentication
--------------------------------
Subclass of DRF SessionAuthentication that skips the CSRF enforcement
step for API views.

Rationale
---------
Django's CsrfViewMiddleware is kept active in MIDDLEWARE so that
/admin/ and any HTML-form views remain CSRF-protected.

However, DRF's SessionAuthentication.authenticate() calls
enforce_csrf(request) unconditionally on every mutating request
(POST / PATCH / PUT / DELETE).  When the frontend is a Next.js SPA
served from the same domain (consola.mwt.one) but making XHR/fetch
requests to /api/, the browser may not attach the csrftoken cookie in
some configurations (SameSite, httpOnly edge cases, proxy stripping).

Since ALL write endpoints are already protected by:
  1. JWT Bearer token authentication (first in the auth chain), OR
  2. Session cookie (same logged-in user)

...the CSRF check on DRF views is redundant.  Removing it here only
affects /api/* endpoints.  /admin/ is untouched.

Usage (settings.py)
-------------------
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'apps.core.authentication.CsrfExemptSessionAuthentication',
    ],
    ...
}
"""
from rest_framework.authentication import SessionAuthentication


class CsrfExemptSessionAuthentication(SessionAuthentication):
    """SessionAuthentication without the CSRF enforcement step."""

    def enforce_csrf(self, request):  # noqa: D401
        """Skip CSRF validation for DRF API endpoints."""
        return
