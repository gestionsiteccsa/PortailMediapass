"""Client JSON-RPC pour l'API PMB (PhpMyBibli).

Fournit l'interface entre Django et le serveur PMB : authentification,
recherche catalogue, consultation notices, gestion des comptes lecteurs,
réservations et prolongements.

L'authentification se fait via un certificat client PKCS#12 (fichier .p12).
"""

import atexit
import contextlib
import hashlib
import os
import tempfile
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
from cryptography.hazmat.primitives.serialization import Encoding, NoEncryption, PrivateFormat
from cryptography.hazmat.primitives.serialization.pkcs12 import load_key_and_certificates
from django.conf import settings

_generated_pem_paths: list[str] = []


def _cleanup_pem_files():
    """Nettoie les fichiers .pem temporaires créés lors de l'extraction du certificat.

    Appelée automatiquement au shutdown via ``atexit``.
    """
    for path in _generated_pem_paths:
        with contextlib.suppress(OSError):
            os.unlink(path)


atexit.register(_cleanup_pem_files)


class PMBClientError(Exception):
    """Exception levée lors d'une erreur de communication avec l'API PMB."""

    pass


def _load_cert_from_p12() -> str:
    """Extrait la clé privée et le certificat du fichier .p12 vers un fichier .pem temporaire.

    Returns:
        Chemin absolu vers le fichier .pem temporaire.

    Raises:
        PMBClientError: Si le fichier .p12 est introuvable, illisible ou invalide.
    """
    p12_path = settings.PMB_CERT_PATH
    p12_password = settings.PMB_CERT_PASS

    if not os.path.exists(p12_path):
        raise PMBClientError(f"Certificat introuvable : {p12_path}\nPlacez votre fichier certificat.p12 dans config/certs/")

    try:
        with open(p12_path, "rb") as f:
            p12_data = f.read()
    except OSError as e:
        raise PMBClientError(f"Impossible de lire le certificat {p12_path} : {e}")

    try:
        private_key, certificate, _ = load_key_and_certificates(
            p12_data,
            p12_password.encode("utf-8"),
        )
    except Exception as e:
        raise PMBClientError(f"Echec du chargement du certificat .p12.\nVerifiez le mot de passe dans .env (PMB_CERT_PASS).\nErreur : {e}")

    cert_pem = certificate.public_bytes(Encoding.PEM)
    key_pem = private_key.private_bytes(
        Encoding.PEM,
        PrivateFormat.PKCS8,
        NoEncryption(),
    )

    fd, path = tempfile.mkstemp(suffix=".pem")
    with os.fdopen(fd, "wb") as f:
        f.write(cert_pem)
        f.write(key_pem)
    _generated_pem_paths.append(path)

    return path


_cert_path_cache: str | None = None


def _get_cert_path() -> str:
    """Retourne le chemin du fichier .pem, avec mise en cache.

    Charge le certificat une seule fois et le réutilise tant que
    le fichier .pem temporaire existe sur le disque.

    Returns:
        Chemin absolu vers le fichier .pem.
    """
    global _cert_path_cache
    if _cert_path_cache is None or not os.path.exists(_cert_path_cache):
        _cert_path_cache = _load_cert_from_p12()
    return _cert_path_cache


def call_pmb(method: str, params: list) -> object:
    """Appelle une méthode JSON-RPC de l'API PMB.

    Envoie une requête POST authentifiée par certificat client
    et retourne le résultat parsé.

    Args:
        method: Nom de la méthode PMB (ex: ``pmbesSearch_simpleSearch``).
        params: Liste des paramètres à passer à la méthode.

    Returns:
        Résultat JSON-RPC (dict, list, str selon la méthode).

    Raises:
        PMBClientError: Si le serveur répond avec une erreur HTTP ou JSON-RPC.
    """
    payload = {
        "method": method,
        "params": params,
        "id": 1,
    }
    url = f"{settings.PMB_WS_URL}?source_id={settings.PMB_SOURCE_ID}"
    response = requests.post(
        url,
        json=payload,
        cert=_get_cert_path(),
        verify=True,
        timeout=30,
    )

    if not response.ok:
        raise PMBClientError(f"Erreur {response.status_code} de PMB : {response.text[:1000]}\nURL : {url}")

    data = response.json()

    if data.get("error") is not None:
        raise PMBClientError(f"Erreur PMB : {data['error']}")

    return data.get("result", {})


def call_pmb_raw_text(method: str, params: list) -> str:
    """Appelle une méthode PMB et retourne la réponse brute en texte.

    Utilisée pour le diagnostic, ne lève pas d'exception en cas d'erreur.

    Args:
        method: Nom de la méthode PMB.
        params: Liste des paramètres.

    Returns:
        Réponse brute formatée : ``[status_code] body``.
    """
    payload = {
        "method": method,
        "params": params,
        "id": 1,
    }
    url = f"{settings.PMB_WS_URL}?source_id={settings.PMB_SOURCE_ID}"
    response = requests.post(
        url,
        json=payload,
        cert=_get_cert_path(),
        verify=True,
        timeout=30,
    )
    return f"[{response.status_code}] {response.text[:2000]}"


def search_notices(query: str, search_type: int = 0, page: int = 0, per_page: int = 100) -> dict:
    """Recherche des notices dans le catalogue PMB.

    Effectue une recherche simple, récupère les identifiants des notices,
    puis fetche les détails de chaque notice **en parallèle** via un
    ThreadPoolExecutor (10 workers).

    Args:
        query: Terme de recherche.
        search_type: Type de recherche (0 = tous les champs).
        page: Numéro de page (0-indexed).
        per_page: Nombre de résultats par page (défaut: 100).

    Returns:
        Dictionnaire avec les clés ``total``, ``notices_ids`` et ``records``.
    """
    search = call_pmb("pmbesSearch_simpleSearch", [search_type, query])
    search_id = search["searchId"]
    nb_total = search.get("nbResults", 0)
    raw = call_pmb("pmbesSearch_fetchSearchRecords", [search_id, page * per_page, per_page])

    if isinstance(raw, list):
        raw_records = raw
    elif isinstance(raw, dict):
        raw_records = raw.get("records", raw.get("notices", raw.get("results", [])))
    else:
        raw_records = []

    notice_ids = []
    for r in raw_records:
        if isinstance(r, dict):
            nid = r.get("noticeId") or r.get("id")
        elif isinstance(r, list) and r:
            nid = r[0]
        else:
            nid = None
        if nid:
            notice_ids.append(nid)

    records = []
    with ThreadPoolExecutor(max_workers=10) as executor:
        future_map = {}
        for nid in notice_ids:
            future_map[executor.submit(_fetch_notice_data, nid)] = nid
        for future in as_completed(future_map):
            nid = future_map[future]
            try:
                notice = future.result(timeout=30)
                if notice:
                    records.append(notice)
            except (PMBClientError, TimeoutError):
                records.append(_notice_record(nid, f"Notice {nid}", [], ""))

    id_order = {nid: i for i, nid in enumerate(notice_ids)}
    records.sort(key=lambda r: id_order.get(r.get("notice_id"), 999))

    return {
        "total": nb_total,
        "notices_ids": [r.get("notice_id") for r in records if r.get("notice_id")],
        "records": records,
    }


def _fetch_notice_data(notice_id: int) -> dict:
    """Récupère les données complètes d'une notice.

    Inclut le titre, la vignette et la liste des exemplaires.

    Args:
        notice_id: Identifiant PMB de la notice.

    Returns:
        Dictionnaire représentant la notice (via ``_notice_record``).
    """
    try:
        raw = call_pmb("pmbesNotices_fetchNoticeListFull", [[notice_id]])
    except PMBClientError:
        raise

    title = ""
    thumbnail = ""
    items = []
    if isinstance(raw, list) and raw:
        n = raw[0]
        if isinstance(n, dict):
            admin = n.get("noticeAdministrative") or {}
            thumbnail = str(admin.get("thumbnail_url") or "")
            for item in n.get("noticeItems") or []:
                if isinstance(item, dict):
                    items.append(
                        {
                            "location": item.get("location") or "",
                            "section": item.get("section") or "",
                            "status": item.get("statut") or item.get("situation") or "",
                            "support": item.get("support") or "",
                            "barcode": item.get("cb") or "",
                            "cote": item.get("cote") or "",
                        }
                    )
            if items and items[0]["barcode"]:
                try:
                    item_info = call_pmb("pmbesItems_fetch_item_info", [items[0]["barcode"]])
                    if isinstance(item_info, dict) and item_info.get("title"):
                        title = item_info["title"]
                except PMBClientError:
                    pass
            if not title:
                title = str(n.get("noticeContent") or f"Notice {notice_id}")

    return _notice_record(notice_id, title or f"Notice {notice_id}", items, thumbnail)


def _notice_record(notice_id: int, title: str, items: list, thumbnail: str = "") -> dict:
    """Construit un dictionnaire normalisé pour une notice.

    Args:
        notice_id: Identifiant PMB de la notice.
        title: Titre de la notice.
        items: Liste des exemplaires.
        thumbnail: URL de la vignette.

    Returns:
        Dictionnaire avec les clés ``notice_id``, ``title``, ``thumbnail``,
        ``author``, ``publisher``, ``isbn``, ``summary``, ``items``.
    """
    return {
        "notice_id": notice_id,
        "title": title,
        "thumbnail": thumbnail,
        "author": "",
        "publisher": "",
        "isbn": "",
        "summary": "",
        "items": items,
    }


def get_notice(notice_id: int) -> dict:
    """Récupère les métadonnées d'une notice (titre, auteur, éditeur, ISBN, résumé).

    Args:
        notice_id: Identifiant PMB de la notice.

    Returns:
        Dictionnaire avec les métadonnées de la notice.
    """
    try:
        raw = call_pmb("pmbesNotices_fetchNoticeListFull", [notice_id])
    except PMBClientError as e:
        return _notice_fallback(notice_id, f"ERREUR fetchNoticeListFull: {e}")

    notices = []
    if isinstance(raw, list):
        notices = raw
    elif isinstance(raw, dict):
        notices = raw.get("notices", raw.get("results", raw.get("records", [])))

    if notices:
        n = notices[0]
        if isinstance(n, dict):
            return {
                "notice_id": n.get("noticeId") or n.get("id") or notice_id,
                "title": n.get("title") or n.get("titre") or n.get("name") or "",
                "author": n.get("author") or n.get("auteur") or n.get("authors") or "",
                "publisher": n.get("publisher") or n.get("editeur") or n.get("editor") or "",
                "isbn": n.get("isbn") or "",
                "summary": n.get("resume") or n.get("summary") or n.get("abstract") or "",
            }
        if isinstance(n, list) and len(n) >= 2:
            return {
                "notice_id": n[0],
                "title": str(n[1] or ""),
                "author": str(n[2] or "") if len(n) > 2 else "",
                "publisher": str(n[3] or "") if len(n) > 3 else "",
                "isbn": str(n[4] or "") if len(n) > 4 else "",
                "summary": str(n[5] or "") if len(n) > 5 else "",
            }
        return {"notice_id": notice_id, "title": f"Notice {notice_id} (format: {type(n).__name__})", "author": "", "publisher": "", "isbn": "", "summary": ""}

    return _notice_fallback(notice_id, "liste vide")


def _notice_fallback(notice_id: int, reason: str = "") -> dict:
    """Crée un dictionnaire de notice minimal en cas d'échec de récupération.

    Args:
        notice_id: Identifiant PMB de la notice.
        reason: Raison de l'échec (optionnelle).

    Returns:
        Dictionnaire partiel avec un titre indiquant l'état d'erreur.
    """
    title = f"Notice {notice_id}" if not reason else f"Notice {notice_id} ({reason})"
    return {"notice_id": notice_id, "title": title, "author": "", "publisher": "", "isbn": "", "summary": ""}


def get_items(notice_id: int) -> dict:
    """Récupère la liste des exemplaires d'une notice.

    Args:
        notice_id: Identifiant PMB de la notice.

    Returns:
        Dictionnaire contenant une clé ``items`` avec la liste des exemplaires.
    """
    try:
        raw = call_pmb("pmbesItems_fetch_notice_items", [notice_id])
    except PMBClientError as e:
        return {"items": [], "error": str(e)}

    items_list = []
    if isinstance(raw, dict):
        raw_items = raw.get("items", raw.get("exemplaires", raw.get("results", [])))
    elif isinstance(raw, list):
        raw_items = raw
    else:
        raw_items = []

    for item in raw_items:
        if isinstance(item, dict):
            items_list.append(
                {
                    "location": item.get("location") or item.get("localisation") or item.get("localization") or "",
                    "status": item.get("statut") or item.get("status") or item.get("disponibilite") or "",
                    "barcode": item.get("barcode") or item.get("code_barre") or "",
                }
            )
        elif isinstance(item, list) and len(item) >= 2:
            items_list.append(
                {
                    "location": str(item[1] or "") if len(item) > 1 else "",
                    "status": str(item[2] or "") if len(item) > 2 else "",
                    "barcode": "",
                }
            )

    return {"items": items_list}


def login_emprunteur(login: str, password: str) -> str:
    """Authentifie un emprunteur (méthode plain).

    Args:
        login: Identifiant de l'emprunteur.
        password: Mot de passe en clair.

    Returns:
        Token de session PMB (str).

    Raises:
        PMBClientError: Si les identifiants sont incorrects.
    """
    result = call_pmb("pmbesOPACEmpr_login", [login, password])
    if isinstance(result, str) and result:
        return result
    if isinstance(result, dict):
        sid = result.get("sessionId") or result.get("session_id") or result.get("id")
        if sid:
            return sid
    raise PMBClientError(f"Identifiants incorrects (reponse : {str(result)[:200]})")


def login_emprunteur_md5(login: str, password: str) -> str:
    """Authentifie un emprunteur (méthode MD5).

    Le mot de passe est hashé en MD5 côté client avant envoi.

    Args:
        login: Identifiant de l'emprunteur.
        password: Mot de passe en clair (hashé en MD5 avant envoi).

    Returns:
        Token de session PMB (str).

    Raises:
        PMBClientError: Si les identifiants sont incorrects.
    """
    md5_pass = hashlib.md5(password.encode("utf-8")).hexdigest()
    result = call_pmb("pmbesOPACEmpr_login_md5", [login, md5_pass])
    if isinstance(result, str) and result:
        return result
    if isinstance(result, dict):
        sid = result.get("sessionId") or result.get("session_id") or result.get("id")
        if sid:
            return sid
    raise PMBClientError(f"Identifiants incorrects (md5) : {str(result)[:200]}")


def login_emprunteur_aes(login: str, password: str) -> str:
    """Authentifie un emprunteur (méthode AES).

    Le mot de passe est hashé en MD5, puis chiffré en AES côté serveur.

    Args:
        login: Identifiant de l'emprunteur.
        password: Mot de passe en clair.

    Returns:
        Token de session PMB (str).

    Raises:
        PMBClientError: Si les identifiants sont incorrects.
    """
    md5_pass = hashlib.md5(password.encode("utf-8")).hexdigest()
    result = call_pmb("pmbesOPACEmpr_login_aes", [login, md5_pass])
    if isinstance(result, str) and result:
        return result
    if isinstance(result, dict):
        sid = result.get("sessionId") or result.get("session_id") or result.get("id")
        if sid:
            return sid
    raise PMBClientError(f"Identifiants incorrects (aes) : {str(result)[:200]}")


def test_login_methods(login: str, password: str) -> list[dict]:
    """Teste toutes les méthodes d'authentification PMB.

    Utile pour le diagnostic : teste les 3 méthodes (plain, MD5, AES),
    différentes formes de paramètres, et si un token est obtenu, teste
    les fonctions authentifiées (compte, prêts, réservations).

    Args:
        login: Identifiant de test.
        password: Mot de passe de test.

    Returns:
        Liste de dictionnaires ``{"label": str, "data": str}``
        décrivant chaque appel et son résultat.
    """
    results = []

    def log(label: str, data):
        """Ajoute une entrée au journal des résultats du diagnostic."""
        data_str = str(data)
        results.append({"label": label, "data": data_str[:3000]})

    def safe_call(name: str, *params) -> dict:
        """Appelle une méthode PMB sans lever d'exception.

        Retourne un dictionnaire avec ``_error`` en cas d'échec.
        """
        try:
            r = call_pmb(name, list(params))
            return r
        except Exception as e:
            return {"_error": f"{type(e).__name__}: {e}"}

    SAFE = "✅"
    FAIL = "❌"

    log("=== TEST CONNEXION EMPRUNTEUR ===", f"login={login}, password={'*' * len(password)}")

    # 1) login standard — différentes formes de paramètres
    for params, desc in [
        ([login, password], "[login, password]"),
        ({"login": login, "password": password}, "dict"),
        ((login, password, True), "avec 3e param"),
        ((login, password, False), "avec 3e param false"),
    ]:
        r = safe_call("pmbesOPACEmpr_login", *params)
        icon = SAFE if isinstance(r, (dict, str)) and (not isinstance(r, dict) or "_error" not in r) and r not in (None, "", {}, 0) else FAIL
        log(f"{icon} pmbesOPACEmpr_login({desc})", r)

    # 2) login_md5 — différentes formes
    md5_pass = hashlib.md5(password.encode("utf-8")).hexdigest()
    md5_pass_upper = md5_pass.upper()
    for password_hash, desc in [
        (md5_pass, "md5"),
        (md5_pass_upper, "MD5 (upper)"),
        (md5_pass, "md5_force"),
    ]:
        r = safe_call("pmbesOPACEmpr_login_md5", login, password_hash)
        icon = SAFE if isinstance(r, (dict, str)) and (not isinstance(r, dict) or "_error" not in r) and r not in (None, "", {}, 0) else FAIL
        log(f"{icon} pmbesOPACEmpr_login_md5({desc})", r)

    # 3) login_aes
    r = safe_call("pmbesOPACEmpr_login_aes", login, md5_pass)
    icon = SAFE if isinstance(r, (dict, str)) and (not isinstance(r, dict) or "_error" not in r) and r not in (None, "", {}, 0) else FAIL
    log(f"{icon} pmbesOPACEmpr_login_aes(login, md5)", r)

    # 4) Méthodes de vérification de compte
    r = safe_call("pmbesOPACEmpr_account_exists", login)
    log(f"{SAFE if isinstance(r, (dict, str)) and (not isinstance(r, dict) or '_error' not in r) else FAIL} pmbesOPACEmpr_account_exists({login})", r)

    for method in ["checkAuth", "check_session", "is_empr", "can_login"]:
        r = safe_call(f"pmbesOPACEmpr_{method}", login)
        log(f"{SAFE if isinstance(r, (dict, str)) and (not isinstance(r, dict) or '_error' not in r) else FAIL} pmbesOPACEmpr_{method}({login})", r)

    # 5) Si login OK, tester les fonctions authentifiées avec le token
    token = None
    for r in results:
        if r["label"].startswith(f"{SAFE} pmbesOPACEmpr_login([login, password])"):
            val = r["data"]
            if isinstance(val, str) and val and not val.startswith("{"):
                token = val
            break

    if token:
        log("\n=== FONCTIONS AUTHENTIFIEES (token obtenu) ===", f"token={token[:20]}...")
        for method in [
            "get_account_info",
            "list_loans",
            "list_resas",
            "getReadingLists",
            "getPublicReadingLists",
            "can_reserve_notice",
        ]:
            r = safe_call(f"pmbesOPACEmpr_{method}", token)
            icon = SAFE if isinstance(r, (dict, str)) and (not isinstance(r, dict) or "_error" not in r) and r not in (None, "", {}, 0) else FAIL
            log(f"{icon} pmbesOPACEmpr_{method}", r)

        for method in ["fetch_empr", "statut_list", "categ_list", "location_list"]:
            r = safe_call(f"pmbesEmpr_{method}", token)
            icon = SAFE if isinstance(r, (dict, str)) and (not isinstance(r, dict) or "_error" not in r) and r not in (None, "", {}, 0) else FAIL
            log(f"{icon} pmbesEmpr_{method} (avec token)", r)

    return results


def logout_emprunteur(session_token: str) -> None:
    """Déconnecte un emprunteur (invalide le token de session).

    Args:
        session_token: Token de session PMB à invalider.
    """
    call_pmb("pmbesOPACEmpr_logout", [session_token])


def get_account_infos(session_token: str) -> dict:
    """Récupère les informations personnelles d'un emprunteur.

    Args:
        session_token: Token de session PMB.

    Returns:
        Dictionnaire avec les clés ``last_name``, ``first_name``, ``email``,
        ``address``, ``zipcode``, ``city``, ``card_number``,
        ``membership_start``, ``membership_end``.
        Retourne un dict vide si la réponse est inattendue.
    """
    raw = call_pmb("pmbesOPACEmpr_get_account_info", [session_token])
    if isinstance(raw, dict):
        perso = raw.get("personal_information") or {}
        return {
            "last_name": perso.get("lastname") or raw.get("lastname") or raw.get("nom") or "",
            "first_name": perso.get("firstname") or raw.get("firstname") or raw.get("prenom") or "",
            "email": perso.get("email") or raw.get("email") or raw.get("mail") or "",
            "address": perso.get("address_part1") or raw.get("adr1") or raw.get("address") or "",
            "zipcode": perso.get("address_cp") or raw.get("code_postal") or raw.get("zipcode") or "",
            "city": perso.get("address_city") or raw.get("ville") or raw.get("city") or "",
            "card_number": perso.get("cb") or raw.get("cb") or raw.get("num_carte") or raw.get("card_number") or "",
            "membership_start": (
                perso.get("date_adhesion")
                or raw.get("date_adhesion")
                or perso.get("adhesion_date")
                or raw.get("adhesion_date")
                or perso.get("date_inscription")
                or raw.get("date_inscription")
                or raw.get("membership_start")
                or ""
            ),
            "membership_end": (
                perso.get("date_expiration")
                or raw.get("date_expiration")
                or perso.get("expiration_date")
                or raw.get("expiration_date")
                or perso.get("date_fin_adhesion")
                or raw.get("date_fin_adhesion")
                or raw.get("membership_end")
                or ""
            ),
        }
    return {}


def get_loans(session_token: str) -> list:
    """Récupère la liste des prêts en cours d'un emprunteur.

    Args:
        session_token: Token de session PMB.

    Returns:
        Liste des prêts (liste vide si aucun prêt ou réponse inattendue).
    """
    result = call_pmb("pmbesOPACEmpr_list_loans", [session_token, 0, 999])
    if result is None:
        return []
    if isinstance(result, list):
        return result
    if isinstance(result, dict):
        for key in ("loans", "prets", "data", "list", "items", "results", "records", "documents"):
            val = result.get(key)
            if isinstance(val, list):
                return val
        for val in result.values():
            if isinstance(val, list):
                return val
        return []
    return []


def get_loans_from_empr(card_number: str) -> list:
    """Récupère les prêts à partir du numéro de carte d'emprunteur.

    Utilise la méthode admin ``pmbesEmpr_fetch_empr`` (nécessite les droits).

    Args:
        card_number: Numéro de carte de l'emprunteur.

    Returns:
        Liste des prêts (liste vide si non trouvé ou erreur API).
    """
    try:
        result = call_pmb("pmbesEmpr_fetch_empr", [card_number])
        if isinstance(result, dict) and result.get("status") and isinstance(result.get("data"), dict):
            prets = result["data"].get("prets", [])
            if isinstance(prets, list):
                return prets
        return []
    except PMBClientError:
        return []


def get_reservations(session_token: str) -> list:
    """Récupère la liste des réservations d'un emprunteur.

    Args:
        session_token: Token de session PMB.

    Returns:
        Liste des réservations (liste vide si aucune).
    """
    result = call_pmb("pmbesOPACEmpr_list_resas", [session_token])
    if result is None:
        return []
    if isinstance(result, list):
        return result
    if isinstance(result, dict):
        return result.get("reservations") or result.get("resas") or result.get("data") or []
    return []


def get_loan_history(session_token: str) -> list:
    """Récupère l'historique des prêts d'un emprunteur.

    Args:
        session_token: Token de session PMB.

    Returns:
        Liste des prêts historiques (liste vide si non disponible ou erreur).
    """
    try:
        result = call_pmb("pmbesOPACEmpr_list_loan_history", [session_token])
        if isinstance(result, list):
            return result
        if isinstance(result, dict):
            return result.get("history") or result.get("anciens_prets") or result.get("loans") or result.get("data") or []
    except PMBClientError:
        pass
    return []


def make_reservation(session_token: str, notice_id: int) -> dict:
    """Réserve une notice pour un emprunteur.

    Args:
        session_token: Token de session PMB.
        notice_id: Identifiant de la notice à réserver.

    Returns:
        Résultat de l'API PMB (dict).
    """
    return call_pmb("pmbesOPACEmpr_makeReservation", [session_token, notice_id])


def renew_loan(session_token: str, loan_id: int) -> dict:
    """Prolonge la durée d'un prêt.

    Args:
        session_token: Token de session PMB.
        loan_id: Identifiant du prêt à prolonger.

    Returns:
        Résultat de l'API PMB (dict).
    """
    return call_pmb("pmbesOPACEmpr_renewLoan", [session_token, loan_id])


def change_password(session_token: str, old_password: str, new_password: str) -> dict:
    """Change le mot de passe d'un emprunteur.

    Args:
        session_token: Token de session PMB.
        old_password: Ancien mot de passe.
        new_password: Nouveau mot de passe.

    Returns:
        Résultat de l'API PMB (dict).

    Raises:
        PMBClientError: Si l'ancien mot de passe est incorrect ou l'appel échoue.
    """
    return call_pmb("pmbesOPACEmpr_change_password", [session_token, old_password, new_password])


def reset_password(card_number: str, new_password: str) -> dict:
    """Réinitialise le mot de passe d'un emprunteur via l'API admin PMB.

    Tente d'appeler ``pmbesEmpr_update_empr`` avec différents formats
    de paramètres pour mettre à jour le mot de passe sans connaître
    l'ancien. Nécessite que le certificat client ait les droits admin.

    Args:
        card_number: Numéro de carte de l'emprunteur.
        new_password: Nouveau mot de passe à définir.

    Returns:
        Résultat de l'API PMB (dict).

    Raises:
        PMBClientError: Si l'appel échoue (API non disponible, droits insuffisants).
    """
    for params in (
        [card_number, {"password": new_password}],
        [card_number, new_password],
        {"empr_id": card_number, "password": new_password},
    ):
        try:
            return call_pmb("pmbesEmpr_update_empr", [card_number, {"password": new_password}])
        except PMBClientError:
            continue
    raise PMBClientError("Impossible de réinitialiser le mot de passe via l'API PMB.")


# ───────────────────────────────
# DIAGNOSTIC PMB
# ───────────────────────────────


def test_pmb_functions() -> list[dict]:
    """Teste exhaustivement toutes les fonctions de l'API PMB.

    Parcourt tous les groupes de méthodes PMB disponibles (Search, Items,
    Notices, Authors, Publishers, etc.) et enregistre le résultat de
    chaque appel. Les méthodes destructrices ou nécessitant une
    authentification sont sautées.

    Utilisé par les pages de diagnostic ``/pmb-diagnostic/``.

    Returns:
        Liste de dictionnaires ``{"label": str, "data": str}``
        décrivant chaque appel et son résultat.
    """
    results = []

    def log(label: str, data):
        """Ajoute une entrée au journal des résultats du diagnostic."""
        data_str = str(data)
        results.append({"label": label, "data": data_str[:3000]})

    def safe_call(method: str, *params) -> dict:
        """Appelle une méthode PMB sans lever d'exception.

        Retourne un dict avec ``_error`` en cas d'échec.
        """
        try:
            r = call_pmb(method, list(params))
            return r
        except Exception as e:
            return {"_error": f"{type(e).__name__}: {e}"}

    SAFE = "✅"
    FAIL = "❌"
    SKIP = "⏭️"

    SKIP_METHODS = {
        "delete",
        "update",
        "clean",
        "login",
        "logout",
        "change_password",
        "self_",
        "add_",
        "remove_",
        "edit_",
        "empty_",
        "create_",
        "import_basic",
        "mysqlTable",
        "executeProc",
        "hashEmprPassword",
        "reindexRecords",
        "genArk",
        "genDocnumThumbnail",
        "checkdelnotice",
        "nettoyage",
        "flushBannette",
        "fillBannette",
        "doSync",
        "emptySource",
        "diffuseBannette",
        "exportBannette",
        "sentDiffusion",
        "sentProduct",
        "sentDiffusionAuto",
        "launchBackup",
        "deleteSauvPerformed",
        "timeoutTasks",
        "runTasks",
        "checkTasks",
        "update",
        "convert_to_utf8",
        "checkExternalAuthentication",
        "get_loans_printer_template",
        "get_printers_config",
    }

    def should_skip(name: str) -> bool:
        """Détermine si une méthode doit être sautée (destructrice ou nécessitant auth)."""
        name_lower = name.lower()
        return any(name_lower.startswith(s) or name_lower == s for s in SKIP_METHODS)

    def test_method(group: str, method: str, *param_sets):
        """Teste une méthode PMB avec différents jeux de paramètres.

        Args:
            group: Groupe PMB (ex: ``pmbesSearch``).
            method: Nom de la méthode (ex: ``simpleSearch``).
            param_sets: Un ou plusieurs tuples de paramètres à tester.
        """
        full = f"{group}_{method}"
        if should_skip(method):
            log(f"{SKIP} {full}", "SAUTE (destructeur / auth requise)")
            return
        for params in param_sets:
            label = f"{full} {list(params)}"
            r = safe_call(full, *params)
            icon = SAFE if isinstance(r, dict) and "_error" not in r and r is not None else FAIL
            if icon == FAIL and isinstance(r, dict) and "_error" in r and "500" in r["_error"]:
                icon = "💀"
            log(f"{icon} {label}", r)

    NOTICE_ID = 93688
    AUTHOR_ID = 1
    PUBLISHER_ID = 1
    COLLECTION_ID = 1
    LOCATION_ID = 1
    SECTION_ID = 1
    BARCODE = "764035961"

    search = safe_call("pmbesSearch_simpleSearch", 0, "harry potter")
    SID = search.get("searchId", "")

    log("=== RECHERCHE ===", f"searchId={SID}, nbResults={search.get('nbResults', 0)}")

    # ── pmbesSearch (17) ──
    log("\n=== pmbesSearch ===", "")
    test_method("pmbesSearch", "simpleSearch", (0, "harry potter"))
    test_method("pmbesSearch", "simpleSearchLocalise", (0, "harry potter", 5, 167))
    test_method("pmbesSearch", "getAdvancedSearchFields", ())
    test_method("pmbesSearch", "getAdvancedSearchField", ("all_fields",))
    test_method("pmbesSearch", "advancedSearch", (0, "harry potter"))
    test_method("pmbesSearch", "get_sort_types", ())
    test_method("pmbesSearch", "fetchSearchRecords", (SID, 0, 3))
    test_method("pmbesSearch", "fetchSearchRecordsSorted", (SID, 0, 3))
    test_method("pmbesSearch", "fetchSearchRecordsArray", (SID, 0, 3))
    test_method("pmbesSearch", "fetchSearchRecordsArraySorted", (SID, 0, 3))
    test_method("pmbesSearch", "fetchSearchRecordsFull", (SID, 0, 3))
    test_method("pmbesSearch", "fetchSearchRecordsFullSorted", (SID, 0, 3))
    test_method("pmbesSearch", "fetchSearchRecordsFullWithBullId", (SID, 0, 3))
    test_method("pmbesSearch", "fetchSearchRecordsFullWithBullIdSorted", (SID, 0, 3))
    test_method("pmbesSearch", "listExternalSources", ())
    test_method("pmbesSearch", "listFacets", (SID,))
    test_method("pmbesSearch", "listRecordsFromFacets", (SID,))

    # ── pmbesItems (5) ──
    log("\n=== pmbesItems ===", "")
    test_method("pmbesItems", "fetch_notice_items", (NOTICE_ID,))
    test_method("pmbesItems", "fetch_notices_items", ([NOTICE_ID],))
    test_method("pmbesItems", "fetch_bulletins_items", ([NOTICE_ID],))
    test_method("pmbesItems", "fetch_item", (BARCODE,))
    test_method("pmbesItems", "fetch_item_info", (BARCODE,))

    # ── pmbesNotices (20) ──
    log("\n=== pmbesNotices ===", "")
    test_method("pmbesNotices", "fetchNoticeList", (NOTICE_ID,))
    test_method("pmbesNotices", "fetchNoticeList", ([NOTICE_ID],))
    test_method("pmbesNotices", "fetchNoticeList", (NOTICE_ID, 0))
    test_method("pmbesNotices", "fetchNoticeList", (NOTICE_ID, 1))
    test_method("pmbesNotices", "fetchExternalNoticeList", (NOTICE_ID,))
    test_method("pmbesNotices", "fetchExternalNoticeList", ([NOTICE_ID],))
    test_method("pmbesNotices", "fetchNoticeListArray", (NOTICE_ID,))
    test_method("pmbesNotices", "fetchNoticeListArray", ([NOTICE_ID],))
    test_method("pmbesNotices", "listNoticeExplNums", (NOTICE_ID,))
    test_method("pmbesNotices", "listNoticeExplNums", ([NOTICE_ID],))
    test_method("pmbesNotices", "listNoticesExplNums", ([NOTICE_ID],))
    test_method("pmbesNotices", "listBulletinExplNums", (NOTICE_ID,))
    test_method("pmbesNotices", "listBulletinExplNums", ([NOTICE_ID],))
    test_method("pmbesNotices", "listBulletinsExplNums", ([NOTICE_ID],))
    test_method("pmbesNotices", "fetchNoticeByExplCb", (BARCODE,))
    test_method("pmbesNotices", "fetch_notices_bulletins", ([NOTICE_ID],))
    test_method("pmbesNotices", "fetchNoticeListFull", (NOTICE_ID,))
    test_method("pmbesNotices", "fetchNoticeListFull", ([NOTICE_ID],))
    test_method("pmbesNotices", "fetchNoticeListFull", ([NOTICE_ID], 0))
    test_method("pmbesNotices", "fetchNoticeListFull", ([NOTICE_ID], 1))
    test_method("pmbesNotices", "fetch_bulletin_list", (NOTICE_ID,))
    test_method("pmbesNotices", "findNoticeBulletinId", (NOTICE_ID,))
    test_method("pmbesNotices", "fetchBulletinListFull", (NOTICE_ID,))
    test_method("pmbesNotices", "fetchBulletinListFull", ([NOTICE_ID],))
    test_method("pmbesNotices", "fetchNoticesCollstates", (NOTICE_ID,))
    test_method("pmbesNotices", "fetchNoticesCollstates", ([NOTICE_ID],))
    test_method("pmbesNotices", "fetchSerialList", ())
    test_method("pmbesNotices", "fetchNoticeListFullWithBullId", ([NOTICE_ID],))
    test_method("pmbesNotices", "fetchNoticesBulletinsList", ([NOTICE_ID],))
    test_method("pmbesNotices", "fetchNoticesAdministrative", (NOTICE_ID,))
    test_method("pmbesNotices", "fetchNoticesAdministrative", ([NOTICE_ID],))
    test_method("pmbesNotices", "checkdelnotice", (NOTICE_ID,))

    # ── pmbesAI (2) ──
    log("\n=== pmbesAI ===", "")
    test_method("pmbesAI", "getDocnumsContent", (NOTICE_ID,))
    test_method("pmbesAI", "getDocnumsContent", ([NOTICE_ID],))
    test_method("pmbesAI", "getSummariesContent", (NOTICE_ID,))
    test_method("pmbesAI", "getSummariesContent", ([NOTICE_ID],))
    test_method("pmbesAI", "getSummariesContent", ([NOTICE_ID, NOTICE_ID + 1],))
    test_method("pmbesAI", "getSummariesContent", ({"notice_ids": [NOTICE_ID]},))

    # ── pmbesAuthors (3) ──
    log("\n=== pmbesAuthors ===", "")
    test_method("pmbesAuthors", "get_author_information", (AUTHOR_ID,))
    test_method("pmbesAuthors", "list_author_notices", (AUTHOR_ID,))
    test_method("pmbesAuthors", "get_author_information_and_notices", (AUTHOR_ID,))

    # ── pmbesPublishers (3) ──
    log("\n=== pmbesPublishers ===", "")
    test_method("pmbesPublishers", "get_publisher_information", (PUBLISHER_ID,))
    test_method("pmbesPublishers", "list_publisher_notices", (PUBLISHER_ID,))
    test_method("pmbesPublishers", "get_publisher_information_and_notices", (PUBLISHER_ID,))

    # ── pmbesCollections (7) ──
    log("\n=== pmbesCollections ===", "")
    test_method("pmbesCollections", "get_collection_information", (COLLECTION_ID,))
    test_method("pmbesCollections", "get_subcollection_information", (COLLECTION_ID,))
    test_method("pmbesCollections", "list_collection_notices", (COLLECTION_ID,))
    test_method("pmbesCollections", "list_collection_subcollections", (COLLECTION_ID,))
    test_method("pmbesCollections", "list_subcollection_notices", (COLLECTION_ID,))
    test_method("pmbesCollections", "get_collection_information_and_notices", (COLLECTION_ID,))
    test_method("pmbesCollections", "get_subcollection_information_and_notices", (COLLECTION_ID,))

    # ── pmbesOPACGeneric (13) ──
    log("\n=== pmbesOPACGeneric ===", "")
    test_method("pmbesOPACGeneric", "list_shelves", ())
    test_method("pmbesOPACGeneric", "list_shelves", (NOTICE_ID,))
    test_method("pmbesOPACGeneric", "retrieve_shelf_content", (1,))
    test_method("pmbesOPACGeneric", "retrieve_shelf_content", ("1",))
    test_method("pmbesOPACGeneric", "list_locations", ())
    test_method("pmbesOPACGeneric", "get_location_information", (LOCATION_ID,))
    test_method("pmbesOPACGeneric", "get_location_information_and_sections", (LOCATION_ID,))
    test_method("pmbesOPACGeneric", "list_sections", ())
    test_method("pmbesOPACGeneric", "get_section_information", (SECTION_ID,))
    test_method("pmbesOPACGeneric", "get_all_locations_and_sections", ())
    test_method("pmbesOPACGeneric", "is_also_borrowed_enabled", ())
    test_method("pmbesOPACGeneric", "also_borrowed", (NOTICE_ID,))
    test_method("pmbesOPACGeneric", "get_infopage", ("index",))
    test_method("pmbesOPACGeneric", "get_marc_table", ())
    test_method("pmbesOPACGeneric", "get_marc_table", ("unimarc",))
    test_method("pmbesOPACGeneric", "selector", (NOTICE_ID,))
    test_method("pmbesOPACGeneric", "selector", (SID,))

    # ── pmbesOPACAnonymous (29+) ──
    log("\n=== pmbesOPACAnonymous ===", "")
    test_method("pmbesOPACAnonymous", "simpleSearch", (0, "harry potter"))
    test_method("pmbesOPACAnonymous", "simpleSearchLocalise", (0, "harry potter", 5, 167))
    test_method("pmbesOPACAnonymous", "getAdvancedSearchFields", ())
    test_method("pmbesOPACAnonymous", "getAdvancedExternalSearchFields", ())
    test_method("pmbesOPACAnonymous", "advancedSearch", (0, "harry potter"))
    test_method("pmbesOPACAnonymous", "advancedSearchExternal", ())
    test_method("pmbesOPACAnonymous", "get_sort_types", ())
    test_method("pmbesOPACAnonymous", "fetchSearchRecords", (SID, 0, 3))
    test_method("pmbesOPACAnonymous", "fetchSearchRecordsSorted", (SID, 0, 3))
    test_method("pmbesOPACAnonymous", "fetchSearchRecordsArray", (SID, 0, 3))
    test_method("pmbesOPACAnonymous", "fetchSearchRecordsArraySorted", (SID, 0, 3))
    test_method("pmbesOPACAnonymous", "fetch_notice_items", (NOTICE_ID,))
    test_method("pmbesOPACAnonymous", "listNoticeExplNums", (NOTICE_ID,))
    test_method("pmbesOPACAnonymous", "listBulletinExplNums", (NOTICE_ID,))
    test_method("pmbesOPACAnonymous", "fetchNoticeList", (NOTICE_ID,))
    test_method("pmbesOPACAnonymous", "fetchNoticeList", ([NOTICE_ID],))
    test_method("pmbesOPACAnonymous", "fetchNoticeListArray", (NOTICE_ID,))
    test_method("pmbesOPACAnonymous", "fetchNoticeListArray", ([NOTICE_ID],))
    test_method("pmbesOPACAnonymous", "fetchNoticeListFull", (NOTICE_ID,))
    test_method("pmbesOPACAnonymous", "fetchNoticeListFull", ([NOTICE_ID],))
    test_method("pmbesOPACAnonymous", "fetchExternalNoticeList", (NOTICE_ID,))
    test_method("pmbesOPACAnonymous", "fetchExternalNoticeList", ([NOTICE_ID],))
    test_method("pmbesOPACAnonymous", "fetchBulletinListFull", ([NOTICE_ID],))
    test_method("pmbesOPACAnonymous", "findNoticeBulletinId", (NOTICE_ID,))
    test_method("pmbesOPACAnonymous", "fetchNoticeByExplCb", (BARCODE,))
    test_method("pmbesOPACAnonymous", "get_author_information_and_notices", (AUTHOR_ID,))
    test_method("pmbesOPACAnonymous", "get_collection_information_and_notices", (COLLECTION_ID,))
    test_method("pmbesOPACAnonymous", "get_subcollection_information_and_notices", (COLLECTION_ID,))
    test_method("pmbesOPACAnonymous", "get_publisher_information_and_notices", (PUBLISHER_ID,))
    test_method("pmbesOPACAnonymous", "list_thesauri", ())
    test_method("pmbesOPACAnonymous", "fetch_thesaurus_node_full", (1,))
    test_method("pmbesOPACAnonymous", "fetch_notices_bulletins", ([NOTICE_ID],))
    test_method("pmbesOPACAnonymous", "fetchNoticesCollstates", (NOTICE_ID,))
    test_method("pmbesOPACAnonymous", "list_shelves", ())
    test_method("pmbesOPACAnonymous", "retrieve_shelf_content", (1,))
    test_method("pmbesOPACAnonymous", "fetchNoticeListFullWithBullId", ([NOTICE_ID],))
    test_method("pmbesOPACAnonymous", "fetchNoticesBulletinsList", ([NOTICE_ID],))
    test_method("pmbesOPACAnonymous", "fetchSearchRecordsFull", (SID, 0, 3))
    test_method("pmbesOPACAnonymous", "fetchSearchRecordsFullSorted", (SID, 0, 3))
    test_method("pmbesOPACAnonymous", "fetchSearchRecordsFullWithBullId", (SID, 0, 3))
    test_method("pmbesOPACAnonymous", "fetchSearchRecordsFullWithBullIdSorted", (SID, 0, 3))
    test_method("pmbesOPACAnonymous", "fetchSerialList", ())
    test_method("pmbesOPACAnonymous", "listExternalSources", ())
    test_method("pmbesOPACAnonymous", "listFacets", (SID,))
    test_method("pmbesOPACAnonymous", "listRecordsFromFacets", (SID,))

    # ── pmbesOPACEmpr (limitée: on saute login/self/etc) ──
    log("\n=== pmbesOPACEmpr (sans auth) ===", "")
    test_method("pmbesOPACEmpr", "list_locations", ())
    test_method("pmbesOPACEmpr", "list_suggestion_categories", ())
    test_method("pmbesOPACEmpr", "list_suggestion_sources", ())
    test_method("pmbesOPACEmpr", "list_suggestion_sources_and_categories", ())
    test_method("pmbesOPACEmpr", "list_resa_locations", ())
    test_method("pmbesOPACEmpr", "can_reserve_notice", (NOTICE_ID,))
    test_method("pmbesOPACEmpr", "list_shelves", ())
    test_method("pmbesOPACEmpr", "retrieve_shelf_content", (1,))
    test_method("pmbesOPACEmpr", "simpleSearch", (0, "harry potter"))
    test_method("pmbesOPACEmpr", "getAdvancedSearchFields", ())
    test_method("pmbesOPACEmpr", "advancedSearch", (0, "harry potter"))
    test_method("pmbesOPACEmpr", "get_sort_types", ())
    test_method("pmbesOPACEmpr", "fetchSearchRecords", (SID, 0, 3))
    test_method("pmbesOPACEmpr", "fetchSearchRecordsSorted", (SID, 0, 3))
    test_method("pmbesOPACEmpr", "fetchSearchRecordsArray", (SID, 0, 3))
    test_method("pmbesOPACEmpr", "fetchSearchRecordsArraySorted", (SID, 0, 3))
    test_method("pmbesOPACEmpr", "fetch_notice_items", (NOTICE_ID,))
    test_method("pmbesOPACEmpr", "fetch_item", (BARCODE,))
    test_method("pmbesOPACEmpr", "listNoticeExplNums", (NOTICE_ID,))
    test_method("pmbesOPACEmpr", "listBulletinExplNums", (NOTICE_ID,))
    test_method("pmbesOPACEmpr", "fetchNoticeList", (NOTICE_ID,))
    test_method("pmbesOPACEmpr", "fetchNoticeListFull", ([NOTICE_ID],))
    test_method("pmbesOPACEmpr", "fetchExternalNoticeList", (NOTICE_ID,))
    test_method("pmbesOPACEmpr", "findNoticeBulletinId", (NOTICE_ID,))
    test_method("pmbesOPACEmpr", "fetchNoticeByExplCb", (BARCODE,))
    test_method("pmbesOPACEmpr", "get_author_information_and_notices", (AUTHOR_ID,))
    test_method("pmbesOPACEmpr", "get_collection_information_and_notices", (COLLECTION_ID,))
    test_method("pmbesOPACEmpr", "get_subcollection_information_and_notices", (COLLECTION_ID,))
    test_method("pmbesOPACEmpr", "get_publisher_information_and_notices", (PUBLISHER_ID,))
    test_method("pmbesOPACEmpr", "list_thesauri", ())
    test_method("pmbesOPACEmpr", "fetch_thesaurus_node_full", (1,))
    test_method("pmbesOPACEmpr", "fetchNoticesCollstates", (NOTICE_ID,))
    test_method("pmbesOPACEmpr", "fetch_notices_bulletins", ([NOTICE_ID],))
    test_method("pmbesOPACEmpr", "fetchSerialList", ())
    test_method("pmbesOPACEmpr", "listExternalSources", ())
    test_method("pmbesOPACEmpr", "fetchNoticeListFullWithBullId", ([NOTICE_ID],))
    test_method("pmbesOPACEmpr", "fetchNoticesBulletinsList", ([NOTICE_ID],))
    test_method("pmbesOPACEmpr", "fetchSearchRecordsFull", (SID, 0, 3))
    test_method("pmbesOPACEmpr", "fetchSearchRecordsFullSorted", (SID, 0, 3))
    test_method("pmbesOPACEmpr", "fetchSearchRecordsFullWithBullId", (SID, 0, 3))
    test_method("pmbesOPACEmpr", "fetchSearchRecordsFullWithBullIdSorted", (SID, 0, 3))
    test_method("pmbesOPACEmpr", "fetchBulletinListFull", ([NOTICE_ID],))
    test_method("pmbesOPACEmpr", "getReadingLists", ())
    test_method("pmbesOPACEmpr", "getPublicReadingLists", ())
    test_method("pmbesOPACEmpr", "listFacets", (SID,))
    test_method("pmbesOPACEmpr", "listRecordsFromFacets", (SID,))

    # ── pmbesSelfServices (sauf destructeurs) ──
    log("\n=== pmbesSelfServices (sans auth) ===", "")

    # ── pmbesConvertImport ──
    log("\n=== pmbesConvertImport ===", "")
    test_method("pmbesConvertImport", "get_convert_types", ())
    test_method("pmbesConvertImport", "convert", (48, NOTICE_ID))
    test_method("pmbesConvertImport", "convert", (48, [NOTICE_ID]))
    test_method("pmbesConvertImport", "convert", ("unimarc", "html", [NOTICE_ID]))
    test_method("pmbesConvertImport", "convert_by_path", ("48", NOTICE_ID))
    test_method("pmbesConvertImport", "convert_by_path", (NOTICE_ID, "48"))

    # ── pmbesCommons ──
    log("\n=== pmbesCommons ===", "")
    test_method("pmbesCommons", "get_unimarc_labels", ())

    # ── pmbesThesauri ──
    log("\n=== pmbesThesauri ===", "")
    test_method("pmbesThesauri", "list_thesauri", ())
    test_method("pmbesThesauri", "fetch_node", (1,))
    test_method("pmbesThesauri", "fetch_node_notice_ids", (1,))
    test_method("pmbesThesauri", "fetch_node_full", (1,))

    # ── pmbesRepositories ──
    log("\n=== pmbesRepositories ===", "")
    test_method("pmbesRepositories", "list_agnostic_repositories", ())

    # ── pmbesAutLinks ──
    log("\n=== pmbesAutLinks ===", "")
    test_method("pmbesAutLinks", "getLinks", (NOTICE_ID,))

    # ── pmbesDatabase ──
    log("\n=== pmbesDatabase ===", "")
    test_method("pmbesDatabase", "get_version_informations", ())
    test_method("pmbesDatabase", "need_update", ())
    test_method("pmbesDatabase", "is_utf8", ())

    # ── pmbesOPACStats ──
    log("\n=== pmbesOPACStats ===", "")
    test_method("pmbesOPACStats", "listView", ())
    test_method("pmbesOPACStats", "getStatopacView", (1,))

    # ── pmbesChklnk (sauf update) ──
    log("\n=== pmbesChklnk ===", "")
    for chk in [
        "check_records",
        "check_records_thumbnail",
        "check_records_custom_fields",
        "check_records_enum",
        "check_bulletins",
        "check_custom_fields_etatcoll",
        "check_authors",
        "check_publishers",
        "check_collections",
        "check_subcollections",
        "check_authorities_thumbnail",
        "check_editorial_custom_fields",
    ]:
        test_method("pmbesChklnk", chk, (50,))

    # ── pmbesPNB ──
    log("\n=== pmbesPNB ===", "")

    # ── pmbesAccessRights ──
    log("\n=== pmbesAccessRights ===", "")
    for ar in [
        "user_notice",
        "empr_notice",
        "empr_docnum",
        "empr_contribution_area",
        "empr_contribution_scenario",
        "contribution_moderator_empr",
        "empr_cms_section",
        "empr_cms_article",
    ]:
        test_method("pmbesAccessRights", ar, (NOTICE_ID,))

    # ── pmbesIndex ──
    log("\n=== pmbesIndex ===", "")

    # ── pmbesScanDocnum ──
    log("\n=== pmbesScanDocnum ===", "")
    test_method("pmbesScanDocnum", "get_doc_num", (NOTICE_ID,))

    # ── pmbesDocwatches ──
    log("\n=== pmbesDocwatches ===", "")

    # ── pmbesCairn ──
    log("\n=== pmbesCairn ===", "")
    test_method("pmbesCairn", "check_token", ("test",))

    # ── pmbesContributions ──
    log("\n=== pmbesContributions ===", "")
    test_method("pmbesContributions", "integrate_entity", ("test",))

    # ── pmbesMailing ──
    log("\n=== pmbesMailing ===", "")

    # ── pmbesEmpr ──
    log("\n=== pmbesEmpr (sans auth) ===", "")
    test_method("pmbesEmpr", "statut_list", ())
    test_method("pmbesEmpr", "categ_list", ())
    test_method("pmbesEmpr", "codestat_list", ())
    test_method("pmbesEmpr", "lang_list", ())
    test_method("pmbesEmpr", "groupe_list", ())
    test_method("pmbesEmpr", "abt_list", ())
    test_method("pmbesEmpr", "location_list", ())
    test_method("pmbesEmpr", "pperso_list_type_values", ())
    test_method("pmbesEmpr", "fetch_empr", (1,))

    # ── pmbesProcs ──
    log("\n=== pmbesProcs ===", "")

    # ── pmbesMySQL ──
    log("\n=== pmbesMySQL ===", "")

    # ── pmbesTasks ──
    log("\n=== pmbesTasks ===", "")
    test_method("pmbesTasks", "listTasksPlanned", ())
    test_method("pmbesTasks", "listTypesTasks", ())
    test_method("pmbesTasks", "getInfoTaskPlanned", (1,))

    # ── pmbesBackup ──
    log("\n=== pmbesBackup ===", "")
    test_method("pmbesBackup", "listGroupsTables", ())
    test_method("pmbesBackup", "listTablesUnsaved", ())
    test_method("pmbesBackup", "listSetBackup", ())
    test_method("pmbesBackup", "listSauvPerformed", ())

    # ── pmbesDSI ──
    log("\n=== pmbesDSI ===", "")
    test_method("pmbesDSI", "listBannettesAuto", ())
    test_method("pmbesDSI", "diffuseBannettesFullAuto", ())
    test_method("pmbesDSI", "diffuseBannetteFullAuto", (1,))

    # ── pmbesSync ──
    log("\n=== pmbesSync ===", "")
    test_method("pmbesSync", "listEntrepotSources", ())

    # ── pmbesClean ──
    log("\n=== pmbesClean (sauf destructeurs) ===", "")
    test_method("pmbesClean", "cleanRelations", ())
    test_method("pmbesClean", "cleanCategoriesPath", ())

    # ── pmbesIndex ──
    log("\n=== pmbesIndex ===", "")

    return results
