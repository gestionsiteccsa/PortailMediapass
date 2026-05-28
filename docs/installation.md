# Installation

## Prérequis

-   Python 3.12
-   Un certificat client PMB au format PKCS#12 (`.p12`)

## 1. Cloner le dépôt

```bash
git clone <url-du-depot> mediapass
cd mediapass
```

## 2. Créer l'environnement virtuel

```bash
python -m venv env
source env/bin/activate  # Linux/Mac
# ou
env\Scripts\activate     # Windows
```

## 3. Installer les dépendances

```bash
pip install -r requirements.txt
```

## 4. Configuration

Créer un fichier `.env` à la racine du projet :

```env
DJANGO_SECRET_KEY="votre-cle-secrete-django"
DJANGO_DEBUG=True
PMB_CERT_PASS="mot-de-passe-du-certificat"
```

Variables optionnelles :

-   `DJANGO_ALLOWED_HOSTS` (défaut : localhost, 127.0.0.1, domaines de production)

## 5. Certificat client

Placer le fichier `.p12` dans `config/certs/certificat.p12`.

!!! note
    Le dossier `config/certs/` est ignoré par git (`.gitignore`).

## 6. Migrations Django

```bash
python manage.py migrate
```

Crée les tables de session et d'authentification Django dans `db.sqlite3`.

## 7. Lancer le serveur

```bash
python manage.py runserver
```

Accès : [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
