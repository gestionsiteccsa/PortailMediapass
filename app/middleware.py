"""Middlewares personnalisés Django.

- ``SecurityHeadersMiddleware`` : ajoute les en-têtes de sécurité CSP en production
- ``RateLimitMiddleware`` : limite le nombre de tentatives sur les pages sensibles
"""

import time

from django.conf import settings
from django.http import HttpResponseForbidden


class SecurityHeadersMiddleware:
    """Ajoute l'en-tête Content-Security-Policy aux réponses en production.

    Limite les sources autorisées pour les scripts, styles, polices,
    images et connexions afin de prévenir les attaques XSS.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        """Ajoute les en-têtes de sécurité à la réponse."""
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
    """Limite le nombre de requêtes sur les pages de connexion et diagnostic.

    Autorise 10 tentatives par intervalle de 5 minutes par adresse IP.
    Les tentatives sont stockées dans la session Django.
    """

    RATE_LIMITS = {
        "login": (10, 300),
    }

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        """Vérifie et applique le rate limiting sur les pages sensibles."""
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
