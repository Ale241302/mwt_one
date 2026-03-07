from django.http import HttpResponseRedirect
from django.views.decorators.http import require_http_methods
from .services import QRResolver

@require_http_methods(["GET"])
def public_qr_redirect_view(request, slug):
    target_url = QRResolver.resolve_and_log(slug, request)
    return HttpResponseRedirect(target_url)
