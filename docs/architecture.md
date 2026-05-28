# Architecture

## Vue d'ensemble

```
┌──────────────┐     HTTP (TLS)     ┌──────────────────────┐
│  Navigateur  │ ──────────────────>│  Django (Mediapass)  │
│  Utilisateur │ <──────────────────│  portail.web         │
└──────────────┘     HTML + CSS     └──────┬───────────────┘
                                           │
                                    JSON-RPC (HTTPS)
                                    Certificat client .p12
                                           │
                                    ┌──────▼───────────────┐
                                    │  PMB (PhpMyBibli)    │
                                    │  serveur API         │
                                    └──────────────────────┘
```

## Flux de données

### Recherche catalogue

1. L'utilisateur saisit une requête de recherche
2. `home/views.py:catalogue()` → `search_notices(query, type, page)`
3. `pmb_client.py:search_notices()` :
    - Appelle `pmbesSearch_simpleSearch` pour obtenir un `searchId`
    - Appelle `pmbesSearch_fetchSearchRecords` pour les IDs de notices
    - Lance `ThreadPoolExecutor(10)` pour fetcher les notices en parallèle
    - Retourne les notices triées

### Authentification lecteur

1. L'utilisateur soumet login + mot de passe
2. `home/views.py:login_view()` → `login_emprunteur(login, password)`
3. `pmb_client.py` teste 3 méthodes : plain, MD5, AES
4. Le token de session PMB est stocké dans `request.session["pmb_token"]`

### Compte lecteur

1. Le token est récupéré depuis la session Django
2. `get_account_infos(token)` → infos personnelles
3. `get_loans_from_empr(card_number)` → prêts en cours
4. `get_reservations(token)` → réservations actives
5. `get_loan_history(token)` → historique des prêts

## Structure du projet

```
Mediapass/
├── app/                    # Projet Django (settings, urls, wsgi)
│   ├── settings.py         # Configuration (151 lignes)
│   ├── middleware.py       # SecurityHeaders + RateLimit
│   └── urls.py             # URLs racine
├── home/                   # Application unique
│   ├── views.py            # 8 vues fonctionnelles
│   ├── urls.py             # 8 routes
│   ├── services/
│   │   └── pmb_client.py   # Client API PMB (916 lignes)
│   └── templates/home/     # 5 templates
├── config/certs/           # Certificat .p12 (ignoré par git)
├── templates/              # Templates globaux
│   └── base.html           # Layout principal
├── docs/                   # Documentation MkDocs
├── .agents/skills/         # Skills pour agents IA
├── manage.py               # Entrypoint Django
└── pyproject.toml          # Configuration outils
```

## Sécurité

-   **Certificat client** : authentification PKCS#12 pour l'API PMB
-   **Rate limiting** : 10 tentatives / 5 minutes sur les pages de login
-   **En-têtes HTTP** : CSP, HSTS, X-Frame-Options en production
-   **Diagnostics** : `/pmb-diagnostic/` et `/pmb-diagnostic-login/` réservés aux `staff`
