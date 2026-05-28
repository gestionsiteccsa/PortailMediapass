import time

from django.conf import settings
from django.http import HttpResponseForbidden


class SecurityHeadersMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if not settings.DEBUG:
            response["Content-Security-Policy"] = (
                "default-src 'self'; "
                "script-src 'self' https://cdn.tailwindcss.com; "
                "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
                "font-src https://fonts.gstatic.com; "
                "img-src 'self' data: https:; "
                "connect-src 'self'; "
                "frame-ancestors 'none'; "
                "base-uri 'self'; "
                "object-src 'none'"
            )
        return response


class RateLimitMiddleware:
    RATE_LIMITS = {
        "login": (10, 300),
    }

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path_info
        if path in ("/login/", "/pmb-diagnostic/", "/pmb-diagnostic-login/"):
            ip = request.META.get("REMOTE_ADDR", "unknown")
            key = f"ratelimit_{path}_{ip}"
            now = time.time()
            history = request.session.get(key, [])
            history = [t for t in history if now - t < 300]
            if len(history) >= 10:
                return HttpResponseForbidden("Trop de tentatives. Réessayez dans 5 minutes.")
            history.append(now)
            request.session[key] = history
        return self.get_response(request)
