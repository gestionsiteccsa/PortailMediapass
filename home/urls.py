"""Configuration des URLs de l'application ``home``.

Définit 8 routes nommées sous le namespace ``home:``.
Toutes les vues sont fonctionnelles.
"""

from django.urls import path

from home.views import (
    catalogue,
    changer_mot_de_passe_view,
    home,
    login_view,
    logout_view,
    mon_compte,
    notice_detail,
    pmb_diagnostic,
    pmb_diagnostic_login,
)

app_name = "home"

urlpatterns = [
    path("", home, name="home"),
    path("catalogue/", catalogue, name="catalogue"),
    path("notice/<int:notice_id>/", notice_detail, name="notice_detail"),
    path("login/", login_view, name="login"),
    path("logout/", logout_view, name="logout"),
    path("compte/", mon_compte, name="mon_compte"),
    path("changer-mot-de-passe/", changer_mot_de_passe_view, name="changer_mot_de_passe"),
    path("pmb-diagnostic/", pmb_diagnostic, name="pmb_diagnostic"),
    path("pmb-diagnostic-login/", pmb_diagnostic_login, name="pmb_diagnostic_login"),
]
