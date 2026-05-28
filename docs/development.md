# Développement

## Commandes essentielles

```bash
# Lancer le serveur de développement
python manage.py runserver

# Linter + formateur
ruff check .
ruff format .

# Vérification de typage
mypy .

# Tests
pytest

# Documentation (serveur avec hot-reload)
mkdocs serve

# Générer la documentation statique
mkdocs build
```

## Conventions de code

### Style
-   Respecter les conventions **PEP 8** via `ruff`
-   Utiliser des **type hints** (Python 3.12)
-   Limite de ligne : **120 caractères**
-   Pas de commentaires superflus — privilégier le code expressif

### Docstrings (Google style)

Toute fonction publique doit avoir une docstring au format Google :

```python
def ma_fonction(param1: str, param2: int) -> bool:
    """Description courte de la fonction.

    Description détaillée si nécessaire, sur plusieurs lignes.

    Args:
        param1: Description du premier paramètre.
        param2: Description du second paramètre.

    Returns:
        Description de la valeur de retour.

    Raises:
        ValueError: Description de la condition d'erreur.
    """
```

### Nommage
-   Variables/fonctions : `snake_case`
-   Constantes : `SCREAMING_SNAKE_CASE`
-   Classes : `PascalCase`
-   Fonctions privées : préfixe `_ma_fonction`

### Imports
Ordre des imports (vérifié par `ruff`) :
1.  Standard library
2.  Tiers (Django, requests, etc.)
3.  Projet (`home.*`)

## Pré-commit hooks

```bash
pre-commit install
```

Les hooks exécutent automatiquement `ruff` et `mypy` avant chaque commit.

## CI/CD

La pipeline GitHub Actions (`./github/workflows/ci.yml`) exécute :

1.  `ruff check .`
2.  `ruff format --check .`
3.  `mypy .`
4.  `pytest`
5.  `mkdocs build --strict`

Sur push sur `main` / `master`, la documentation est déployée sur GitHub Pages.

## Documentation auto-générée

La documentation API est extraite des docstrings par `mkdocstrings` :

```bash
mkdocs serve    # prévisualisation temps réel
mkdocs build    # génération dans site/
```

Pour ajouter une nouvelle page de doc :

1.  Créer un fichier `.md` dans `docs/`
2.  Ajouter une entrée dans `nav:` de `mkdocs.yml`

Pour documenter un nouveau module Python :

1.  Écrire les docstrings (Google style) dans le code
2.  Créer une page Markdown avec `::: mon.module` pour l'inclure
