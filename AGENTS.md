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
home/                 — single Django app, all logic lives here
home/services/pmb_client.py  — PMB API client (880 loc), the core
home/views.py         — 8 functional views (no class-based views)
home/templates/home/  — per-view templates
templates/base.html   — base layout
debug_pmb.py          — standalone script to test PMB API directly
PMB.md                — config guide for the PMB API integration
PMB_API.md            — reference of all tested PMB API functions
```

## PMB API client (`home/services/pmb_client.py`)
- Reads `.p12` cert from `settings.PMB_CERT_PATH`, extracts key/cert to temp `.pem` for `requests`
- `call_pmb(method, params)` — generic JSON-RPC caller
- `search_notices()` uses `ThreadPoolExecutor` (10 workers) for parallel notice detail fetches
- 3 auth methods implemented: plain, MD5, AES
- Run diagnostics at `/pmb-diagnostic/` and `/pmb-diagnostic-login/`

## No tests / no lint / no CI
- `home/tests.py` is empty, `home/migrations/` has only `__init__.py`
- No `pyproject.toml`, no lint/formatter config
- No CI/CD pipeline

## Dependencies
Managed through the virtual environment at `env/`. No `requirements.txt` — use `pip list` to inspect. Key packages: Django 6.0.5, requests, cryptography, zeep (installed but unused), python-dotenv.

## Key settings
- `DEBUG` from `DJANGO_DEBUG` env var (True in dev)
- SQLite (`db.sqlite3`) for Django session/auth tables
- `TIME_ZONE = 'Europe/Paris'`
- HTTPS security settings (`SECURE_SSL_REDIRECT`, HSTS, etc.) only active when `DEBUG=False`
- Diagnostics (`/pmb-diagnostic/`, `/pmb-diagnostic-login/`) restricted to staff users
