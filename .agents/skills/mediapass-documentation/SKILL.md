# Mediapass Documentation Skill

## Contexte

Projet Django 6.0.5 — portail de bibliothèque publique interface PMB.
Code en français, vues fonctionnelles, pas de DRF, Tailwind CDN.

## Stack documentation

- **Docstrings** : Google style (``Args:``, ``Returns:``, ``Raises:``)
- **MkDocs** : ``mkdocs serve`` (hot-reload), ``mkdocs build`` (génération)
- **mkdocstrings** : extraction auto des docstrings vers les pages API
- **Thème** : Material, français

## Commandes

```bash
mkdocs serve              # Serveur dev avec auto-reload
mkdocs build              # Générer le site statique dans site/
mkdocs build --strict     # Build strict (erreur si warning)
ruff check .              # Linter
ruff format .             # Formatteur
mypy .                    # Vérification de typage
pytest                    # Tests
pre-commit run --all-files # Hooks pre-commit
```

## Conventions documentation

1. Toute fonction publique doit avoir une docstring Google
2. Les docstrings sont en français (comme le projet)
3. Utiliser ``Args:``, ``Returns:``, ``Raises:``
4. Privilégier les types par défaut plutôt que les annotations de type dans la docstring
5. Les fonctions privées (préfixe ``_``) doivent aussi avoir une docstring

## Structure docs/

```
docs/
├── index.md               # Présentation, stack, conventions
├── architecture.md        # Schéma, flux, structure projet
├── installation.md        # Setup, .env, certificat
├── development.md         # Commandes, conventions code
├── deployment.md          # Production, sécurité
└── api/
    ├── pmb_client.md      # Doc auto-générée de pmb_client.py
    ├── views.md           # Doc auto-générée de views.py
    ├── middleware.md       # Doc auto-générée de middleware.py
    └── urls.md            # Doc auto-générée de urls.py
```

## CI/CD

Le fichier ``.github/workflows/ci.yml`` exécute :
- ruff check + format
- mypy
- pytest
- mkdocs build --strict
- Déploiement GitHub Pages sur push main/master
