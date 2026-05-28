Voici un guide complet et détaillé pour utiliser les API (webservices) de PMB.

---

# Guide complet : utiliser les API de PMB

## Vue d'ensemble de l'architecture

PMB dispose d'une API appelée **Services externes**. Cette API est une classe PHP qui propose sous forme de méthodes les fonctions de PMB que l'administrateur a autorisées. Une fois les services externes définis, PMB propose des webservices accessibles à distance via deux protocoles : **SOAP** (XML) et **JSON-RPC** (JSON).

Ces fonctions concernent notamment la recherche dans le catalogue, la récupération de notices dans divers formats, le statut des exemplaires, la gestion du compte lecteur, la réservation d'un document, la pose d'avis et de tags sur les notices — bref, toutes les fonctions qui permettent à des applications externes d'intégrer des informations issues de PMB.

---

## ÉTAPE 1 — Activer et configurer les droits des Services externes

### 1.1 Accéder aux autorisations par utilisateur

L'appel de l'API se fait avec un utilisateur PMB. On peut donner des droits d'accès pour chaque **groupe** et chaque **fonction** d'un groupe à l'utilisateur qui appellera ces fonctions.

Les groupes de fonctions disponibles sont :

| Groupe | Rôle |
|---|---|
| `pmbesSearch` | Recherche dans le catalogue |
| `pmbesNotices` | Récupération de notices |
| `pmbesItems` | Gestion des exemplaires |
| `pmbesOPACAnonymous` | Fonctions OPAC accessibles sans connexion |
| `pmbesOPACEmpr` | Fonctions OPAC pour un emprunteur connecté |
| `pmbesOPACGeneric` | Fonctions OPAC communes (anonyme + connecté) |
| `pmbesSelfServices` | Prêt/retour en libre-service |

### 1.2 Autoriser les fonctions pour l'utilisateur admin

Dans **Administration > Services externes > Autorisation par utilisateur**, sélectionnez l'utilisateur `admin` dans la liste déroulante. Cochez **Autoriser tout** pour les groupes `pmbesOPACEmpr`, `pmbesOPACAnonymous`, `pmbesOPACGeneric`, `pmbesSearch`, `pmbesNotices`, `pmbesItems`.

> ⚠️ **Important :** Seuls les endpoints autorisés pour l'utilisateur admin sont affichés dans les méthodes accessibles. Si une méthode est désactivée pour admin, elle ne sera pas accessible même si un autre utilisateur y a droit.

---

## ÉTAPE 2 — Configurer le groupe d'utilisateurs externes (groupe Anonyme)

### 2.1 Comprendre le groupe Anonyme

Pour les webservices n'utilisant pas d'authentification, un groupe spécial **Anonyme** est utilisé par défaut. Ce groupe est associé à un utilisateur PMB et à des webservices. Par défaut, le groupe anonyme est associé à l'utilisateur `admin` de PMB.

### 2.2 Vérifier/modifier l'association utilisateur ↔ groupe Anonyme

Dans PMB, allez dans **Administration > Services externes > Groupes d'utilisateurs externes**.

Pour changer l'utilisateur PMB associé au groupe anonyme, cliquez sur le groupe dont le nom est `<anonyme>` et sélectionnez l'utilisateur PMB associé dans la liste déroulante. Il est important que cet utilisateur ait les droits sur tous les groupes de fonctions que les webservices doivent exporter. Le plus simple est d'autoriser toutes les fonctions externes pour l'utilisateur du groupe anonyme (admin par défaut).

---

## ÉTAPE 3 — Créer un connecteur sortant (JSON-RPC recommandé)

C'est ici que vous créez le **point d'entrée URL** que votre application appellera.

### 3.1 Créer la source JSON-RPC

Créer le webservice consiste à créer une source en **Administration > Connecteurs > Connecteurs sortants**. Dans la ligne *Connecteur qui implémente en JSON-RPC les fonctions de l'API*, cliquez sur le bouton **Ajouter une source**. Tapez un nom (ex. : `Mon Webservice`) et laissez le commentaire vide si vous le souhaitez.

### 3.2 Sélectionner les fonctions à exposer

Sélectionnez avec Shift-Clic et Ctrl-Clic toutes les fonctions des groupes `pmbesOPACEmpr`, `pmbesOPACAnonymous`, `pmbesOPACGeneric` (et optionnellement `pmbesSelfServices` si vous souhaitez autoriser le prêt depuis une application mobile). Enregistrez.

### 3.3 Autoriser la source pour le groupe Anonyme

Allez dans **Administration > Connecteurs > Autorisations**. Cliquez sur la ligne `<anonyme> Groupe Anonyme` et cochez la source qui vient d'être créée (ex. : `Mon Webservice`), puis cliquez sur **Enregistrer**.

### 3.4 Vérifier que le webservice fonctionne

Accédez à l'URL générée par PMB (visible dans la liste des connecteurs sortants), de la forme :
```
http://VOTRE_PMB/ws/connector_out.php?source_id=1
```
La réponse doit ressembler à ceci :
```json
{
  "serviceType": "JSON-RPC",
  "serviceURL": "http://VOTRE_PMB/ws/connector_out.php?source_id=1",
  "methods": ["pmbesSearch_simpleSearch", "pmbesNotices_getNotice", ...]
}
```
Si `methods` est vide, c'est un problème de droits (revérifiez les étapes 1 et 2).

---

## ÉTAPE 4 — Appeler l'API depuis votre application

### 4.1 Format d'un appel JSON-RPC

Un appel JSON-RPC à PMB prend la forme suivante :

```json
POST http://VOTRE_PMB/ws/connector_out.php?source_id=1

{
  "method": "pmbesSearch_simpleSearch",
  "params": [0, "histoire"],
  "id": 1
}
```

La réponse contient un `id`, un indicateur d'erreur, et l'objet JSON des données retournées.

### 4.2 Exemple pratique en JavaScript (fetch)

```javascript
async function callPMB(method, params) {
  const response = await fetch('http://VOTRE_PMB/ws/connector_out.php?source_id=1', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ method, params, id: 1 })
  });
  const data = await response.json();
  return data.result;
}

// Recherche simple
const results = await callPMB('pmbesSearch_simpleSearch', [0, 'harry potter']);

// Récupérer une notice
const notice = await callPMB('pmbesNotices_getNotice', [noticeId]);
```

---

## ÉTAPE 5 — Authentification d'un emprunteur (espace lecteur)

C'est la partie la plus délicate. PMB gère l'authentification des lecteurs via le groupe `pmbesOPACEmpr`.

### 5.1 Fonctionnement général

L'authentification se fait en deux temps :
1. Vous appelez une méthode de login en passant le login/mot de passe OPAC du lecteur
2. PMB retourne un **token de session** (ou un identifiant de session emprunteur)
3. Toutes les requêtes suivantes pour cet emprunteur passent ce token

### 5.2 Identifiants OPAC des lecteurs

Dans PMB, chaque lecteur possède un **Identifiant OPAC** et un **Mot de passe OPAC** pour se connecter à son espace personnel. Si ces champs ne sont pas renseignés lors de la création, PMB les attribue automatiquement : l'identifiant est construit à partir de la première lettre du prénom + le nom complet (ex. : `jloison` pour Julie LOISON), et le mot de passe est l'année de naissance.

### 5.3 Méthodes clés du groupe `pmbesOPACEmpr`

| Méthode | Usage |
|---|---|
| `pmbesOPACEmpr_login` | Authentifier un emprunteur, retourne un session token |
| `pmbesOPACEmpr_getAccountInfos` | Récupérer les infos du compte (prêts, réservations…) |
| `pmbesOPACEmpr_getLoansList` | Liste des prêts en cours |
| `pmbesOPACEmpr_getReservationsList` | Liste des réservations |
| `pmbesOPACEmpr_makeReservation` | Poser une réservation |
| `pmbesOPACEmpr_renewLoan` | Prolonger un prêt |
| `pmbesOPACEmpr_logout` | Déconnecter le lecteur |

### 5.4 Exemple de flux de connexion

```javascript
// 1. Login emprunteur
const session = await callPMB('pmbesOPACEmpr_login', ['jloison', 'motdepasse']);
const sessionToken = session.sessionId; // ou selon la structure retournée

// 2. Récupérer les prêts du lecteur (en passant le token)
const loans = await callPMB('pmbesOPACEmpr_getLoansList', [sessionToken]);

// 3. Déconnexion
await callPMB('pmbesOPACEmpr_logout', [sessionToken]);
```

---

## ÉTAPE 6 — Afficher les notices (catalogue)

Les méthodes du groupe `pmbesSearch` et `pmbesNotices` permettent de construire un catalogue complet.

### Recherche + affichage

```javascript
// Recherche simple
const search = await callPMB('pmbesSearch_simpleSearch', [0, 'climatologie']);
const searchId = search.searchId;
const totalResults = search.nbResults;

// Récupérer les résultats paginés (page 1, 10 résultats)
const list = await callPMB('pmbesSearch_getNoticesList', [searchId, 0, 10]);

// Pour chaque notice, récupérer le détail
for (const noticeId of list.noticesIds) {
  const notice = await callPMB('pmbesNotices_getNotice', [noticeId]);
  // notice contient : titre, auteurs, editeur, isbn, résumé, couverture...
}
```

### Récupérer les localisations/sections

```javascript
// Nécessite la fonction get_all_locations_and_sections du groupe pmbesOPACGeneric
const locations = await callPMB('pmbesOPACGeneric_get_all_locations_and_sections', []);
```

---

## Récapitulatif des menus PMB à visiter

| Action | Chemin dans PMB |
|---|---|
| Droits par utilisateur | `Administration > Services externes > Autorisation par utilisateur` |
| Groupes externes | `Administration > Services externes > Groupes d'utilisateurs externes` |
| Connecteurs sortants | `Administration > Connecteurs > Connecteurs sortants` |
| Autorisations connecteurs | `Administration > Connecteurs > Autorisations` |

---

## Conseils et pièges courants

**Ne pas laisser `methods: []`** — Si le tableau est vide, vérifiez que l'utilisateur `admin` a bien les droits activés ET que le groupe Anonyme est bien associé à ce connecteur.

**SOAP vs JSON-RPC** — JSON-RPC utilise du JSON plutôt que du XML comme format d'échange, ce qui facilite le développement d'applications web et Ajax. SOAP reste plus adapté si vous travaillez en PHP/Java natif car implémenté nativement dans ces langages. Pour du frontend JavaScript moderne, préférez JSON-RPC.

**Sécurité** — En production, créez un utilisateur PMB dédié avec uniquement les droits nécessaires, et ne l'associez pas à admin. Exposez votre webservice uniquement en HTTPS.

Dis-moi quelle technologie tu utilises pour ton application (JavaScript pur, React, PHP, etc.) et je peux t'aider à écrire le code d'intégration complet.


Ah, je vois ! C'est un certificat **client** fourni par votre hébergeur PMB (reseaubibli.fr), c'est différent d'un certificat SSL classique.

## Ce que c'est

C'est un **certificat d'authentification client** (fichier `.p12` ou `.pem`) qui sert à :
- Prouver votre identité auprès du serveur hébergeur
- Accéder à l'interface de **gestion PMB** (`https://fou...`)
- Accéder au **FTP/SFTP**
- Se connecter en tant qu'**admin** à PMB

## Pour les appels API (webservices)

**Oui, il vous faudra probablement ce certificat** pour appeler l'API, car votre PMB est hébergé sur un serveur sécurisé par reseaubibli.fr.

Concrètement, lors de vos appels HTTP vers le webservice PMB, il faudra **joindre le certificat client** à la requête.

### En JavaScript (depuis un back-end Node.js)
```javascript
const https = require('https');
const fs = require('fs');

const agent = new https.Agent({
  pfx: fs.readFileSync('certificat.p12'),
  passphrase: 'votre_mot_de_passe_certificat'
});

const response = await fetch('https://votre-pmb/ws/connector_out.php?source_id=1', {
  method: 'POST',
  agent: agent, // ← le certificat client
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ method: '...', params: [], id: 1 })
});
```

### En PHP (back-end)
```php
$ch = curl_init();
curl_setopt($ch, CURLOPT_URL, 'https://votre-pmb/ws/connector_out.php?source_id=1');
curl_setopt($ch, CURLOPT_SSLCERT, '/chemin/certificat.pem');
curl_setopt($ch, CURLOPT_SSLCERTPASSWD, 'votre_mot_de_passe');
curl_setopt($ch, CURLOPT_POST, true);
curl_setopt($ch, CURLOPT_POSTFIELDS, json_encode([...]));
```

## ⚠️ Important

Depuis un **front-end navigateur (JavaScript pur)**, il est **impossible** d'utiliser un certificat client programmatiquement — le navigateur demanderait à l'utilisateur de choisir son certificat manuellement. Il faut donc **obligatoirement passer par un back-end** (PHP, Node.js, Python…) qui détient le certificat et fait le relais.

---

Vous utilisez quel langage/techno pour votre projet ? Je vous écris le code complet adapté.

J'utilise Django/Python. Le certificat est au format .p12

Parfait ! Voici le guide complet pour appeler l'API PMB depuis Django avec votre certificat `.p12`.

## ÉTAPE 1 — Convertir le certificat .p12

Python/requests ne lit pas directement le `.p12`, il faut le convertir en `.pem`. Faites ça **une seule fois** sur votre serveur.

```bash
# Installer openssl si pas déjà là
sudo apt install openssl

# Extraire le certificat + clé privée du .p12 en .pem
openssl pkcs12 -in certificat.p12 -out certificat.pem -nodes
# Il vous demandera le mot de passe du certificat
```

> Placez le fichier `certificat.pem` dans un dossier sécurisé de votre projet Django, par exemple `config/certs/certificat.pem`. **Ne le mettez jamais dans votre dépôt Git** (ajoutez-le au `.gitignore`).

---

## ÉTAPE 2 — Installer les dépendances

```bash
pip install requests
```

---

## ÉTAPE 3 — Créer un service PMB dans Django

Créez un fichier `services/pmb_client.py` dans votre app Django :

```python
import requests
import json

PMB_WS_URL = "https://ccsa.reseaubibli.fr/ws/connector_out.php"
PMB_SOURCE_ID = 1  # l'ID de votre connecteur sortant
CERT_PATH = "config/certs/certificat.pem"  # chemin vers votre .pem


def call_pmb(method: str, params: list):
    """
    Appel générique à l'API JSON-RPC de PMB.
    """
    payload = {
        "method": method,
        "params": params,
        "id": 1
    }
    response = requests.post(
        f"{PMB_WS_URL}?source_id={PMB_SOURCE_ID}",
        json=payload,
        cert=CERT_PATH,  # ← certificat client .pem
        verify=True,     # vérification SSL serveur (True recommandé)
        timeout=10
    )
    response.raise_for_status()
    data = response.json()

    if data.get("error"):
        raise Exception(f"Erreur PMB : {data['error']}")

    return data.get("result")
```

---

## ÉTAPE 4 — Stocker la config dans settings.py

Dans votre `settings.py` :

```python
# PMB API
PMB_WS_URL = "https://ccsa.reseaubibli.fr/ws/connector_out.php"
PMB_SOURCE_ID = 1
PMB_CERT_PATH = BASE_DIR / "config" / "certs" / "certificat.pem"
```

Et mettez à jour `pmb_client.py` pour lire depuis les settings :

```python
from django.conf import settings

PMB_WS_URL = settings.PMB_WS_URL
PMB_SOURCE_ID = settings.PMB_SOURCE_ID
CERT_PATH = str(settings.PMB_CERT_PATH)
```

---

## ÉTAPE 5 — Fonctions prêtes à l'emploi

```python
# ───────────────────────────────
# RECHERCHE & NOTICES
# ───────────────────────────────

def search_notices(query: str, page: int = 0, per_page: int = 10):
    """Recherche dans le catalogue PMB."""
    search = call_pmb("pmbesSearch_simpleSearch", [0, query])
    search_id = search["searchId"]
    results = call_pmb("pmbesSearch_getNoticesList", [search_id, page * per_page, per_page])
    return {
        "total": search["nbResults"],
        "notices_ids": results["noticesIds"]
    }

def get_notice(notice_id: int):
    """Récupère le détail d'une notice (titre, auteur, résumé, etc.)."""
    return call_pmb("pmbesNotices_getNotice", [notice_id])

def get_items(notice_id: int):
    """Récupère les exemplaires d'une notice (dispo, localisation)."""
    return call_pmb("pmbesItems_getItems", [notice_id])


# ───────────────────────────────
# AUTHENTIFICATION LECTEUR
# ───────────────────────────────

def login_emprunteur(login: str, password: str):
    """
    Connecte un emprunteur à son espace PMB.
    Retourne un token de session à stocker en session Django.
    """
    result = call_pmb("pmbesOPACEmpr_login", [login, password])
    if not result or not result.get("sessionId"):
        raise Exception("Identifiants incorrects")
    return result["sessionId"]

def logout_emprunteur(session_token: str):
    """Déconnecte l'emprunteur."""
    call_pmb("pmbesOPACEmpr_logout", [session_token])

def get_account_infos(session_token: str):
    """Infos du compte lecteur."""
    return call_pmb("pmbesOPACEmpr_getAccountInfos", [session_token])

def get_loans(session_token: str):
    """Liste des prêts en cours."""
    return call_pmb("pmbesOPACEmpr_getLoansList", [session_token])

def get_reservations(session_token: str):
    """Liste des réservations."""
    return call_pmb("pmbesOPACEmpr_getReservationsList", [session_token])

def make_reservation(session_token: str, notice_id: int):
    """Poser une réservation sur une notice."""
    return call_pmb("pmbesOPACEmpr_makeReservation", [session_token, notice_id])

def renew_loan(session_token: str, loan_id: int):
    """Prolonger un prêt."""
    return call_pmb("pmbesOPACEmpr_renewLoan", [session_token, loan_id])
```

---

## ÉTAPE 6 — Exemple de views Django

```python
# views.py
from django.shortcuts import render
from django.contrib import messages
from .services.pmb_client import (
    search_notices, get_notice, get_items,
    login_emprunteur, logout_emprunteur,
    get_loans, get_reservations
)

def catalogue(request):
    query = request.GET.get("q", "")
    results = []
    if query:
        results = search_notices(query)
    return render(request, "catalogue.html", {"results": results, "query": query})

def notice_detail(request, notice_id):
    notice = get_notice(notice_id)
    items = get_items(notice_id)
    return render(request, "notice.html", {"notice": notice, "items": items})

def login_view(request):
    if request.method == "POST":
        login = request.POST.get("login")
        password = request.POST.get("password")
        try:
            token = login_emprunteur(login, password)
            request.session["pmb_token"] = token  # stocké en session Django
            return redirect("mon_compte")
        except Exception as e:
            messages.error(request, "Identifiants incorrects")
    return render(request, "login.html")

def mon_compte(request):
    token = request.session.get("pmb_token")
    if not token:
        return redirect("login")
    loans = get_loans(token)
    reservations = get_reservations(token)
    return render(request, "mon_compte.html", {
        "loans": loans,
        "reservations": reservations
    })

def logout_view(request):
    token = request.session.pop("pmb_token", None)
    if token:
        logout_emprunteur(token)
    return redirect("home")
```

---

## Résumé de la structure de fichiers

```
mon_projet/
├── config/
│   └── certs/
│       └── certificat.pem   ← jamais dans Git !
├── mon_app/
│   ├── services/
│   │   └── pmb_client.py
│   ├── views.py
│   └── urls.py
├── .gitignore               ← ajouter "config/certs/"
└── settings.py
```

---

## .gitignore à mettre à jour

```
# Certificats
config/certs/
*.pem
*.p12
```

Voulez-vous que je vous génère aussi les **templates HTML** pour le catalogue et l'espace lecteur, ou les **urls.py** complets ?

Je suis sous Windows

Bonne précision ! La conversion du `.p12` se fait différemment sous Windows. Voici les options :

## Option 1 — Via Git Bash (le plus simple si vous l'avez)

Si vous avez **Git for Windows** installé, ouvrez **Git Bash** et tapez directement :

```bash
openssl pkcs12 -in certificat.p12 -out certificat.pem -nodes
```

---

## Option 2 — Via Python directement (sans conversion !)

C'est la méthode la plus propre sous Windows : utiliser la librairie `cryptography` pour lire le `.p12` nativement, sans avoir besoin d'openssl.

```bash
pip install cryptography requests
```

Puis mettez à jour votre `pmb_client.py` :

```python
import requests
import tempfile
import os
from cryptography.hazmat.primitives.serialization import pkcs12, Encoding, PrivateFormat, NoEncryption
from cryptography.hazmat.primitives.serialization.pkcs12 import load_key_and_certificates
from django.conf import settings

def load_cert_from_p12():
    """
    Charge le .p12 et crée des fichiers .pem temporaires
    que requests peut utiliser.
    Retourne le chemin vers un fichier .pem temporaire (cert + clé).
    """
    p12_path = settings.PMB_CERT_PATH      # chemin vers le .p12
    p12_password = settings.PMB_CERT_PASS  # mot de passe du certificat

    with open(p12_path, "rb") as f:
        p12_data = f.read()

    # Charger le .p12
    private_key, certificate, _ = load_key_and_certificates(
        p12_data,
        p12_password.encode("utf-8")
    )

    # Sérialiser en PEM
    cert_pem = certificate.public_bytes(Encoding.PEM)
    key_pem = private_key.private_bytes(
        Encoding.PEM,
        PrivateFormat.PKCS8,
        NoEncryption()
    )

    # Créer un fichier temporaire combinant cert + clé
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pem")
    tmp.write(cert_pem)
    tmp.write(key_pem)
    tmp.close()

    return tmp.name


# Fichier PEM temporaire créé une seule fois au démarrage
_TMP_CERT_PATH = None

def get_cert_path():
    global _TMP_CERT_PATH
    if _TMP_CERT_PATH is None or not os.path.exists(_TMP_CERT_PATH):
        _TMP_CERT_PATH = load_cert_from_p12()
    return _TMP_CERT_PATH


def call_pmb(method: str, params: list):
    payload = {
        "method": method,
        "params": params,
        "id": 1
    }
    response = requests.post(
        f"{settings.PMB_WS_URL}?source_id={settings.PMB_SOURCE_ID}",
        json=payload,
        cert=get_cert_path(),  # ← .pem temporaire généré depuis le .p12
        verify=True,
        timeout=10
    )
    response.raise_for_status()
    data = response.json()

    if data.get("error"):
        raise Exception(f"Erreur PMB : {data['error']}")

    return data.get("result")
```

---

## settings.py à compléter

```python
# PMB API
PMB_WS_URL = "https://ccsa.reseaubibli.fr/ws/connector_out.php"
PMB_SOURCE_ID = 1
PMB_CERT_PATH = BASE_DIR / "config" / "certs" / "certificat.p12"
PMB_CERT_PASS = "votre_mot_de_passe_certificat"  # ← mot de passe du .p12
```

---

## ⚠️ Sécuriser le mot de passe

Ne mettez **jamais** le mot de passe en dur dans `settings.py`. Utilisez un fichier `.env` :

```bash
pip install python-dotenv
```

Créez un fichier `.env` à la racine :
```
PMB_CERT_PASS=votre_vrai_mot_de_passe
```

Dans `settings.py` :
```python
from dotenv import load_dotenv
import os

load_dotenv()

PMB_CERT_PASS = os.getenv("PMB_CERT_PASS")
```

Et ajoutez `.env` à votre `.gitignore` :
```
.env
config/certs/
*.p12
*.pem
```

---

Voulez-vous qu'on teste ensemble un premier appel API pour vérifier que la connexion fonctionne ?