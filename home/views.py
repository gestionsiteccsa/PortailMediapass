"""Vues fonctionnelles du portail Mediapass.

Chaque vue rend un template Django avec les données issues de l'API PMB.

Toutes les vues sont des fonctions (pas de class-based views).
Les vues de diagnostic sont réservées aux utilisateurs staff.
"""

import logging

from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render

from home.services.pmb_client import (
    PMBClientError,
    _fetch_notice_data,
    change_password,
    get_account_infos,
    get_loan_history,
    get_loans_from_empr,
    get_reservations,
    login_emprunteur,
    search_notices,
    test_login_methods,
    test_pmb_functions,
)

logger = logging.getLogger(__name__)


def home(request: HttpRequest) -> HttpResponse:
    """Page d'accueil du portail.

    Affiche une sélection de livres favoris (données statiques en dur)
    et les dernières actualités du réseau.

    Args:
        request: Requête HTTP Django.

    Returns:
        Template ``home/index.html`` avec les contextes
        ``books_favorites`` et ``latest_news``.
    """
    books_favorites = [
        {
            "title": "Les Gardiens du Temps",
            "author": "Élise Moreau",
            "category": "Roman",
            "gradient": "from-amber-600 to-orange-700",
        },
        {
            "title": "L'Énigme du Cosmos",
            "author": "Marc Lefèvre",
            "category": "Science-fiction",
            "gradient": "from-indigo-600 to-purple-800",
        },
        {
            "title": "Chemins de Traverse",
            "author": "Clara Dubois",
            "category": "Voyage",
            "gradient": "from-emerald-500 to-teal-700",
        },
        {
            "title": "Le Jardin des Oubliés",
            "author": "Pierre-André Blanc",
            "category": "Littérature",
            "gradient": "from-rose-500 to-pink-700",
        },
        {
            "title": "Algorithmes et Vertiges",
            "author": "Sophie Lambert",
            "category": "Essai",
            "gradient": "from-cyan-600 to-blue-800",
        },
        {
            "title": "La Nuit des Masques",
            "author": "Victor Tissot",
            "category": "Polar",
            "gradient": "from-slate-700 to-slate-900",
        },
        {
            "title": "Horizons Lointains",
            "author": "Anna Kéruzoré",
            "category": "Aventure",
            "gradient": "from-sky-500 to-blue-700",
        },
        {
            "title": "Mémoires d'Encre",
            "author": "Julien Carpentier",
            "category": "Histoire",
            "gradient": "from-stone-500 to-amber-800",
        },
    ]

    latest_news = [
        {
            "title": "Horaires d'été dans les médiathèques",
            "date": "12 juin 2026",
            "date_iso": "2026-06-12",
            "category": "Infos pratiques",
            "category_color": "bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300",
            "gradient": "from-blue-500 to-cyan-600",
            "excerpt": "Découvrez les nouveaux horaires d'ouverture des bibliothèques du réseau pour la période estivale...",
        },
        {
            "title": "Atelier numérique : Initiation à la BD numérique",
            "date": "8 juin 2026",
            "date_iso": "2026-06-08",
            "category": "Atelier",
            "category_color": "bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300",
            "gradient": "from-emerald-500 to-green-700",
            "excerpt": "Un atelier pour apprendre à créer votre propre bande dessinée avec des outils numériques gratuits.",
        },
        {
            "title": "Exposition : Voyages en Méditerranée",
            "date": "1 juin 2026",
            "date_iso": "2026-06-01",
            "category": "Exposition",
            "category_color": "bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-300",
            "gradient": "from-violet-500 to-purple-700",
            "excerpt": "Photographies et récits de voyage autour de la Méditerranée, du Maroc à la Grèce.",
        },
        {
            "title": "Nouveautés du mois de juin",
            "date": "28 mai 2026",
            "date_iso": "2026-05-28",
            "category": "Sélections",
            "category_color": "bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-300",
            "gradient": "from-amber-500 to-orange-600",
            "excerpt": "Découvrez les dernières acquisitions du réseau : romans, documentaires et livres audio.",
        },
        {
            "title": "Concours de lecture : À vos marques, prêts, lisez !",
            "date": "20 mai 2026",
            "date_iso": "2026-05-20",
            "category": "Événement",
            "category_color": "bg-rose-100 dark:bg-rose-900/30 text-rose-700 dark:text-rose-300",
            "gradient": "from-rose-500 to-pink-600",
            "excerpt": "Participez à notre grand concours de lecture ouvert à tous les adhérents du réseau.",
        },
    ]

    return render(
        request,
        "home/index.html",
        {
            "books_favorites": books_favorites,
            "latest_news": latest_news,
        },
    )


def catalogue(request: HttpRequest) -> HttpResponse:
    """Page de recherche dans le catalogue PMB.

    Lit les paramètres GET ``q`` (requête), ``type`` (type de recherche)
    et ``page`` (numéro de page) pour interroger l'API PMB.

    Args:
        request: Requête HTTP Django.

    Returns:
        Template ``home/catalogue.html`` avec les résultats de recherche.
    """
    query = request.GET.get("q", "")[:500]
    raw_type = request.GET.get("type", "0")
    raw_page = request.GET.get("page", "0")
    try:
        search_type = int(raw_type)
    except (ValueError, TypeError):
        search_type = 0
    try:
        page = int(raw_page)
    except (ValueError, TypeError):
        page = 0
    results: dict = {}
    error: str = ""
    if query:
        try:
            results = search_notices(query, search_type=search_type, page=page, per_page=100)
        except PMBClientError as e:
            logger.warning("PMB catalogue error: %s", e)
            error = "La recherche est temporairement indisponible."
    return render(
        request,
        "home/catalogue.html",
        {
            "query": query,
            "search_type": search_type,
            "results": results,
            "page": page,
            "error": error,
        },
    )


def notice_detail(request: HttpRequest, notice_id: int) -> HttpResponse:
    """Page de détail d'une notice.

    Affiche les informations complètes d'une notice et ses exemplaires.

    Args:
        request: Requête HTTP Django.
        notice_id: Identifiant PMB de la notice.

    Returns:
        Template ``home/notice.html`` ou redirection vers le catalogue
        si la notice est indisponible.
    """
    try:
        notice = _fetch_notice_data(notice_id)
        return render(
            request,
            "home/notice.html",
            {
                "notice": notice,
                "items": {"items": notice.get("items", [])},
            },
        )
    except PMBClientError as e:
        logger.warning("PMB notice error: %s", e)
        messages.error(request, "Notice indisponible.")
        return redirect("home:catalogue")


def login_view(request: HttpRequest) -> HttpResponse:
    """Page de connexion emprunteur.

    En POST : tente d'authentifier l'utilisateur via l'API PMB.
    En GET : affiche le formulaire de connexion.

    Args:
        request: Requête HTTP Django.

    Returns:
        Template ``home/login.html`` ou redirection vers le compte
        en cas de succès.
    """
    if request.method == "POST":
        login = request.POST.get("login", "")
        password = request.POST.get("password", "")
        try:
            token = login_emprunteur(login, password)
            request.session["pmb_token"] = token
            return redirect("home:mon_compte")
        except PMBClientError as e:
            logger.warning("PMB login error: %s", e)
            messages.error(request, "Identifiant ou mot de passe incorrect.")
        except Exception as e:
            logger.error("Unexpected login error: %s", e)
            messages.error(request, "Erreur de connexion. Veuillez réessayer.")
    return render(request, "home/login.html")


def logout_view(request: HttpRequest) -> HttpResponse:
    """Déconnexion de l'utilisateur.

    Supprime le token PMB de la session Django et redirige vers l'accueil.

    Args:
        request: Requête HTTP Django.

    Returns:
        Redirection vers la page d'accueil.
    """
    request.session.pop("pmb_token", None)
    return redirect("home:home")


def mon_compte(request: HttpRequest) -> HttpResponse:
    """Page du compte emprunteur.

    Affiche les informations personnelles, les prêts en cours,
    les réservations et l'historique des prêts.

    Args:
        request: Requête HTTP Django.

    Returns:
        Template ``home/compte.html`` ou redirection vers la page
        de connexion si l'utilisateur n'est pas authentifié.
    """
    token = request.session.get("pmb_token")
    if not token:
        return redirect("home:login")
    try:
        account = get_account_infos(token)
        card_number = account.get("card_number", "")
        loans = get_loans_from_empr(card_number) if card_number else []
        reservations = get_reservations(token)
        loan_history = get_loan_history(token)
        return render(
            request,
            "home/compte.html",
            {
                "account": account,
                "loans": loans,
                "reservations": reservations,
                "loan_history": loan_history,
            },
        )
    except PMBClientError as e:
        logger.warning("PMB account error: %s", e)
        messages.error(request, "Impossible de charger votre compte.")
        return redirect("home:login")


def changer_mot_de_passe_view(request: HttpRequest) -> HttpResponse:
    """Page de changement de mot de passe.

    Permet à l'emprunteur connecté de modifier son mot de passe.
    Valide que les deux saisies du nouveau mot de passe sont identiques
    et que le nouveau mot de passe fait au moins 6 caractères.

    Args:
        request: Requête HTTP Django.

    Returns:
        Template ``home/changer_mot_de_passe.html`` ou redirection
        vers le compte en cas de succès.
    """
    token = request.session.get("pmb_token")
    if not token:
        return redirect("home:login")

    if request.method == "POST":
        old_password = request.POST.get("old_password", "")
        new_password1 = request.POST.get("new_password1", "")
        new_password2 = request.POST.get("new_password2", "")

        if not old_password or not new_password1 or not new_password2:
            messages.error(request, "Tous les champs sont obligatoires.")
            return render(request, "home/changer_mot_de_passe.html")

        if new_password1 != new_password2:
            messages.error(request, "Les nouveaux mots de passe ne sont pas identiques.")
            return render(request, "home/changer_mot_de_passe.html")

        if len(new_password1) < 6:
            messages.error(
                request,
                "Le nouveau mot de passe doit contenir au moins 6 caractères.",
            )
            return render(request, "home/changer_mot_de_passe.html")

        try:
            change_password(token, old_password, new_password1)
            messages.success(request, "Mot de passe modifié avec succès.")
            return redirect("home:mon_compte")
        except PMBClientError as e:
            logger.warning("PMB change password error: %s", e)
            messages.error(request, "Ancien mot de passe incorrect.")
        except Exception as e:
            logger.error("Unexpected change password error: %s", e)
            messages.error(request, "Erreur lors du changement de mot de passe.")

    return render(request, "home/changer_mot_de_passe.html")


@staff_member_required
def pmb_diagnostic(request: HttpRequest) -> HttpResponse:
    """Page de diagnostic PMB (staff uniquement).

    Teste exhaustivement toutes les fonctions de l'API PMB et affiche
    les résultats bruts en HTML. Inclut un formulaire de test de
    connexion emprunteur.

    Args:
        request: Requête HTTP Django.

    Returns:
        HttpResponse HTML avec les résultats du diagnostic.
    """
    login_results = []
    test_login = request.POST.get("test_login", "")
    test_password = request.POST.get("test_password", "")

    if test_login and test_password:
        login_results = test_login_methods(test_login, test_password) or []

    results = test_pmb_functions() or []
    csrf_token = request.COOKIES.get("csrftoken", "")
    html = "<html><head><meta charset='utf-8'><title>Diagnostic PMB</title></head><body>"
    html += "<h1>Diagnostic PMB</h1>"
    html += "<div style='background:#f0f8ff;border:1px solid #ccc;padding:16px;margin:16px 0;border-radius:8px'>"
    html += "<h3>\U0001f511 Test connexion emprunteur</h3>"
    html += f"<form method='POST'><input type='hidden' name='csrfmiddlewaretoken' value='{csrf_token}'>"
    html += "<label>Login : <input type='text' name='test_login' style='margin:4px 8px'></label>"
    html += "<label>Mot de passe : <input type='password' name='test_password' style='margin:4px 8px'></label>"
    html += "<button type='submit' style='padding:4px 16px;cursor:pointer'>Tester</button>"
    html += "</form></div>"

    if login_results:
        html += f"<h2>Résultats connexion ({len(login_results)} tests)</h2><pre>"
        for r in login_results:
            label = r.get("label", "")
            data = r.get("data", "")
            css_class = ""
            if label.startswith("✅"):
                css_class = ' style="color:green"'
            elif label.startswith("❌") or label.startswith("💀"):
                css_class = ' style="color:red"'
            elif label.startswith("==="):
                html += f'\n<div style="background:#eef;padding:4px;margin-top:8px"><b>{label}</b></div>'
                continue
            html += f"\n<div{css_class}>{label}</div>"
            if data and data != "{}":
                html += f'<div style="margin-left:20px;font-size:0.9em">{data[:800]}</div>'
        html += "</pre>"

    html += f"<h2>Fonctions PMB ({len(results)} appels)</h2><pre>"
    for r in results:
        label = r.get("label", "")
        data = r.get("data", "")
        css_class = ""
        if label.startswith("✅"):
            css_class = ' style="color:green"'
        elif label.startswith("❌") or label.startswith("💀"):
            css_class = ' style="color:red"'
        elif label.startswith("⏭️"):
            css_class = ' style="color:gray"'
        elif label.startswith("==="):
            html += f'\n<div style="background:#eee;padding:4px;margin-top:8px"><b>{label}</b></div>'
            continue
        html += f"\n<div{css_class}>{label}</div>"
        if data and data != "{}":
            html += f'<div style="margin-left:20px;font-size:0.9em">{data[:800]}</div>'
    html += "</pre></body></html>"
    return HttpResponse(html)


@staff_member_required
def pmb_diagnostic_login(request: HttpRequest) -> HttpResponse:
    """Page de test des méthodes d'authentification PMB (staff uniquement).

    Interface stylisée pour tester les 3 méthodes de connexion
    (plain, MD5, AES) et visualiser les résultats.

    Args:
        request: Requête HTTP Django.

    Returns:
        HttpResponse HTML avec les résultats de test.
    """
    results = []
    test_login = request.POST.get("login", "")
    test_password = request.POST.get("password", "")
    submitted = bool(test_login and test_password)

    if submitted:
        results = test_login_methods(test_login, test_password) or []

    csrf_token = request.COOKIES.get("csrftoken", "")

    login_val = f'value="{test_login}"' if submitted else ""

    html = "<!DOCTYPE html>\n<html lang='fr'>\n<head><meta charset='utf-8'><title>Test connexion PMB</title>\n<style>"
    html += "body{font-family:monospace;max-width:900px;margin:20px auto;padding:0 16px;background:#f9f9f9}"
    html += "h1{color:#333}.box{background:#fff;border:1px solid #ddd;border-radius:8px;padding:20px;margin:16px 0}"
    html += ".form-row{display:flex;gap:12px;align-items:end;flex-wrap:wrap;margin:12px 0}"
    html += ".form-group{display:flex;flex-direction:column}.form-group label{font-size:0.85em;color:#555;margin-bottom:4px}"
    html += ".form-group input{padding:8px;border:1px solid #ccc;border-radius:4px;width:220px;font-size:1em}"
    html += "button{padding:8px 24px;background:#0066cc;color:#fff;border:none;border-radius:4px;cursor:pointer;font-size:1em}"
    html += "button:hover{background:#0052a3}.success{color:#090;font-weight:bold}.error{color:#c00}"
    html += "pre{margin:4px 0;white-space:pre-wrap;word-break:break-all}"
    html += ".section{background:#eef;padding:6px 10px;margin:12px 0 4px;font-weight:bold;border-radius:4px}"
    html += ".result{margin:4px 0;padding:4px 0;border-bottom:1px solid #eee}"
    html += ".result-data{color:#555;font-size:0.85em;margin-left:24px}"
    html += "</style></head><body>"
    html += "<h1>\U0001f511 Test connexion emprunteur PMB</h1>"
    html += "<div class='box'>"
    html += f"<form method='POST'><input type='hidden' name='csrfmiddlewaretoken' value='{csrf_token}'>"
    html += "<div class='form-row'><div class='form-group'>"
    html += "<label for='login'>Identifiant</label>"
    html += f"<input type='text' id='login' name='login' {login_val} placeholder='ex: 12345' required>"
    html += "</div><div class='form-group'>"
    html += "<label for='password'>Mot de passe</label>"
    html += "<input type='password' id='password' name='password' placeholder='Mot de passe' required>"
    html += "</div><button type='submit'>Tester la connexion</button></div></form></div>"

    if not submitted:
        html += '<div class="box" style="color:#888">Entrez un identifiant et mot de passe pour tester toutes les méthodes de connexion PMB.</div>'
    else:
        html += f'<div class="box"><h3>Résultats pour <strong>{test_login}</strong></h3>'
        has_success = any(r.get("label", "").startswith("✅") for r in results)
        if has_success:
            html += '<p class="success">✅ Au moins une méthode a fonctionné !</p>'
        else:
            html += '<p class="error">❌ Aucune méthode de connexion fonctionnelle.</p>'

        for r in results:
            label = r.get("label", "")
            data = r.get("data", "")
            if label.startswith("==="):
                html += f'<div class="section">{label.replace("===", "").strip()}</div>'
                continue
            css = ""
            if label.startswith("✅"):
                css = 'class="success"'
            elif label.startswith("❌"):
                css = 'class="error"'
            html += f'<div class="result" {css}>{label}</div>'
            if data and data != "{}":
                html += f'<div class="result-data">{data[:1000]}</div>'
        html += "</div>"

        if has_success:
            html += """
<div class="box">
<h4>Session token obtenu ?</h4>
<p>Si une ✅ apparaît ci-dessus, le login fonctionne. Le token de session peut être utilisé
pour tester les autres fonctions pmbesOPACEmpr (compte, prêts, réservations).</p>
</div>"""

    html += """
<div class="box" style="background:#f0f0f0">
<p><a href="/pmb-diagnostic/" target="_blank">→ Voir le diagnostic PMB complet</a></p>
<p><a href="/pmb-diagnostic-login/">→ Réinitialiser le formulaire</a></p>
</div>
</body></html>"""
    return HttpResponse(html)
