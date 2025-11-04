from django.shortcuts import redirect
from django.urls import reverse, resolve
from django.conf import settings

EXEMPT_URL_NAMES = {
    'terms_and_conditions',    # the terms page itself
    'logout',
    'admin:login',             # admin login
    # add names for any API auth endpoints, health checks, etc.
}

def is_exempt_path(request):
    # allow static/media and staff/admin & debug endpoints by path prefix
    if request.path.startswith(settings.STATIC_URL) or getattr(settings, 'MEDIA_URL', None) and request.path.startswith(settings.MEDIA_URL):
        return True
    try:
        view_name = resolve(request.path_info).view_name
    except Exception:
        view_name = None
    if view_name in EXEMPT_URL_NAMES:
        return True
    # allow admin, static, or any explicit extras in settings
    for prefix in getattr(settings, "TERMS_WHITELIST_PREFIXES", []):
        if request.path.startswith(prefix):
            return True
    return False


class TermsCheckMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            if not request.user.agreed_to_terms and request.path not in [
                reverse('terms_and_conditions'),
                reverse('logout'),
            ]:
                return redirect('terms_and_conditions')
        return self.get_response(request)
