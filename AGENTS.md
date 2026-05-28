# Mediapass — AGENTS.md

## Stack
- **Django 6.0.5** (Python 3.12/.python-version) on SQLite, no custom models
- **No DRF** — traditional Django views rendering server-side templates
- **Tailwind CSS v3 via CDN** — no npm, no build step
- **PMB (PhpMyBibli) JSON-RPC API** with PKCS#12 client certificate auth
- **French** throughout (UI, code, docs)

## Quick start
```
python manage.py runserver
```
Dev server requires `.env` with:
- `PMB_CERT_PASS` — PKCS#12 cert password
- `DJANGO_SECRET_KEY` — Django secret key
- `DJANGO_DEBUG=True` — development mode
Plus `config/certs/certificat.p12`.

## Project layout
```
app/settings.py       — project settings (single file)
app/middleware.py     — SecurityHeaders + RateLimit middleware
home/                 — single Django app, all logic lives here
home/services/pmb_client.py  — PMB API client (~920 loc), the core
home/views.py         — 8 functional views (no class-based views)
home/templates/home/  — per-view templates
templates/base.html   — base layout
debug_pmb.py          — standalone script to test PMB API directly
PMB.md                — config guide for the PMB API integration
PMB_API.md            — reference of all tested PMB API functions
docs/                 — MkDocs documentation site
pyproject.toml        — ruff, mypy, pytest configuration
```

## Documentation

### Docstrings (Google style)
All Python modules and functions have Google-style docstrings written in French.
```
def ma_fonction(param1: str, param2: int) -> bool:
    """Description courte.

    Args:
        param1: Description.
        param2: Description.

    Returns:
        Description de la valeur de retour.

    Raises:
        ValueError: Condition d'erreur.
    """
```

### MkDocs — documentation auto-générée
```
mkdocs serve              # Serveur dev avec hot-reload (surveille les .py et .md)
mkdocs build              # Génère site/ statique
mkdocs build --strict     # Build strict (erreur si warning)
```
Les pages API (`docs/api/`) sont auto-générées par `mkdocstrings` à partir des docstrings.

## Quality tools (pyproject.toml)

| Tool     | Command                    | Config                        |
|----------|----------------------------|-------------------------------|
| **ruff** | `ruff check .`             | PEP 8, Google docstring conv  |
| **ruff** | `ruff format .`            | Formateur automatique         |
| **mypy** | `mypy .`                   | Typage statique               |
| **pytest** | `pytest`                 | pytest-django                 |
| **pre-commit** | `pre-commit run --all-files` | ruff + mypy avant commit |

## CI/CD
- `.github/workflows/ci.yml` — runs ruff, mypy, pytest, mkdocs build on push/PR
- Docs auto-deployed to GitHub Pages on push to main/master

## PMB API client (`home/services/pmb_client.py`)
- Reads `.p12` cert from `settings.PMB_CERT_PATH`, extracts key/cert to temp `.pem` for `requests`
- `call_pmb(method, params)` — generic JSON-RPC caller
- `search_notices()` uses `ThreadPoolExecutor` (10 workers) for parallel notice detail fetches
- 3 auth methods implemented: plain, MD5, AES
- Run diagnostics at `/pmb-diagnostic/` and `/pmb-diagnostic-login/`

## Dependencies
Managed through `requirements.txt`. Key packages: Django 6.0.5, requests, cryptography, python-dotenv, mkdocs, mkdocstrings, ruff, mypy, pytest, pre-commit.

## Key settings
- `DEBUG` from `DJANGO_DEBUG` env var (True in dev)
- SQLite (`db.sqlite3`) for Django session/auth tables
- `TIME_ZONE = 'Europe/Paris'`
- HTTPS security settings (`SECURE_SSL_REDIRECT`, HSTS, etc.) only active when `DEBUG=False`
- Diagnostics (`/pmb-diagnostic/`, `/pmb-diagnostic-login/`) restricted to staff users

## Skills
- `.agents/skills/mediapass-documentation/` — documentation conventions & commands
- All other `.agents/skills/` are generic opencode skills
