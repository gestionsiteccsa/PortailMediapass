# Déploiement

## Prérequis production

-   Python 3.12
-   Serveur WSGI (Gunicorn, uWSGI) ou ASGI (Daphne, Uvicorn)
-   Serveur HTTP proxy (Nginx, Caddy)
-   Certificat SSL/TLS
-   Certificat client `.p12` pour l'API PMB

## Variables d'environnement

```env
DJANGO_SECRET_KEY="<cle-secrete-tres-longue>"
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS="domaine.fr,www.domaine.fr"
PMB_CERT_PASS="<mot-de-passe>"
```

## Sécurité en production

Quand `DJANGO_DEBUG=False`, Django active automatiquement :

-   `SECURE_SSL_REDIRECT = True`
-   `SESSION_COOKIE_SECURE = True`
-   `CSRF_COOKIE_SECURE = True`
-   `SECURE_HSTS_SECONDS = 31536000` (1 an)
-   `SECURE_HSTS_INCLUDE_SUBDOMAINS = True`
-   `SECURE_HSTS_PRELOAD = True`
-   `SECURE_CONTENT_TYPE_NOSNIFF = True`
-   `SECURE_BROWSER_XSS_FILTER = True`
-   `X_FRAME_OPTIONS = 'DENY'`

Le middleware `SecurityHeadersMiddleware` ajoute en plus :

-   `Content-Security-Policy` (scripts, styles, polices)

## Diagnostic

En production, les pages de diagnostic sont accessibles uniquement
aux utilisateurs `staff` (champ `is_staff=True` dans l'admin Django) :

-   `/pmb-diagnostic/` — test exhaustif de toutes les fonctions PMB
-   `/pmb-diagnostic-login/` — test des méthodes d'authentification
