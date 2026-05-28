"""Tests du module de changement de mot de passe."""

from unittest.mock import patch

import pytest
from django.contrib.messages import get_messages
from django.test import Client
from django.urls import reverse

from home.services.pmb_client import PMBClientError

pytestmark = pytest.mark.django_db


class TestChangePasswordClient:
    """Tests unitaires de la fonction change_password dans pmb_client.py."""

    def test_change_password_appelle_call_pmb(self):
        """Vérifie que change_password appelle call_pmb avec les bons paramètres."""
        from home.services.pmb_client import change_password

        with patch("home.services.pmb_client.call_pmb") as mock_call:
            mock_call.return_value = {"success": True}
            result = change_password("token123", "old_pass", "new_pass")

        mock_call.assert_called_once_with(
            "pmbesOPACEmpr_change_password",
            ["token123", "old_pass", "new_pass"],
        )
        assert result == {"success": True}

    def test_change_password_propage_erreur(self):
        """Vérifie que PMBClientError est propagée."""
        from home.services.pmb_client import change_password

        with patch("home.services.pmb_client.call_pmb") as mock_call:
            mock_call.side_effect = PMBClientError("Erreur PMB")
            with pytest.raises(PMBClientError, match="Erreur PMB"):
                change_password("token", "old", "new")


class TestChangePasswordView:
    """Tests de la vue de changement de mot de passe."""

    def test_get_sans_token_redirige_login(self):
        """GET sans session token → redirect login."""
        client = Client()
        url = reverse("home:changer_mot_de_passe")
        response = client.get(url)
        assert response.status_code == 302
        assert response.url == reverse("home:login")

    def test_get_avec_token_affiche_formulaire(self):
        """GET avec session token → 200 + template."""
        client = Client()
        session = client.session
        session["pmb_token"] = "token123"
        session.save()
        url = reverse("home:changer_mot_de_passe")
        response = client.get(url)
        assert response.status_code == 200
        assert any("changer_mot_de_passe" in t.name for t in response.templates)

    def test_post_sans_token_redirige_login(self):
        """POST sans session token → redirect login."""
        client = Client()
        url = reverse("home:changer_mot_de_passe")
        response = client.post(url, {"old_password": "a", "new_password1": "b", "new_password2": "b"})
        assert response.status_code == 302
        assert response.url == reverse("home:login")

    def test_post_nouveaux_mots_de_passe_differents(self):
        """POST avec new_password1 != new_password2 → erreur + 200."""
        client = Client()
        session = client.session
        session["pmb_token"] = "token123"
        session.save()

        with patch("home.views.change_password") as mock_change:
            url = reverse("home:changer_mot_de_passe")
            response = client.post(
                url,
                {
                    "old_password": "old",
                    "new_password1": "newpass1",
                    "new_password2": "newpass2",
                },
                follow=True,
            )

        mock_change.assert_not_called()
        assert response.status_code == 200
        messages = list(get_messages(response.wsgi_request))
        assert any("identiques" in str(m) for m in messages)

    def test_post_nouveau_mot_de_passe_trop_court(self):
        """POST avec nouveau mot de passe < 6 caractères → erreur."""
        client = Client()
        session = client.session
        session["pmb_token"] = "token123"
        session.save()

        with patch("home.views.change_password") as mock_change:
            url = reverse("home:changer_mot_de_passe")
            response = client.post(
                url,
                {
                    "old_password": "old",
                    "new_password1": "ab",
                    "new_password2": "ab",
                },
                follow=True,
            )

        mock_change.assert_not_called()
        assert response.status_code == 200
        messages = list(get_messages(response.wsgi_request))
        assert any("6" in str(m) for m in messages)

    def test_post_succes(self):
        """POST valide → appelle change_password + redirect + message succès."""
        client = Client()
        session = client.session
        session["pmb_token"] = "token123"
        session.save()

        patches = [
            patch("home.views.change_password", return_value={"success": True}),
            patch("home.views.get_account_infos", return_value={"card_number": "123"}),
            patch("home.views.get_loans_from_empr", return_value=[]),
            patch("home.views.get_reservations", return_value=[]),
            patch("home.views.get_loan_history", return_value=[]),
        ]
        with patches[0] as mock_change, patches[1], patches[2], patches[3], patches[4]:
            url = reverse("home:changer_mot_de_passe")
            response = client.post(
                url,
                {
                    "old_password": "old",
                    "new_password1": "newpassword",
                    "new_password2": "newpassword",
                },
                follow=True,
            )

        mock_change.assert_called_once_with("token123", "old", "newpassword")
        assert response.status_code == 200
        assert response.redirect_chain[-1][0] == reverse("home:mon_compte")
        messages = list(get_messages(response.wsgi_request))
        assert any("succès" in str(m).lower() for m in messages)

    def test_post_ancien_mot_de_passe_incorrect(self):
        """POST avec ancien MDP erroné → erreur PMB + message."""
        client = Client()
        session = client.session
        session["pmb_token"] = "token123"
        session.save()

        with patch("home.views.change_password") as mock_change:
            mock_change.side_effect = PMBClientError("Ancien mot de passe incorrect")
            url = reverse("home:changer_mot_de_passe")
            response = client.post(
                url,
                {
                    "old_password": "wrong",
                    "new_password1": "newpassword",
                    "new_password2": "newpassword",
                },
                follow=True,
            )

        assert response.status_code == 200
        messages = list(get_messages(response.wsgi_request))
        assert any("incorrect" in str(m).lower() for m in messages)

    def test_post_champs_vides(self):
        """POST avec des champs vides → erreur de validation."""
        client = Client()
        session = client.session
        session["pmb_token"] = "token123"
        session.save()

        with patch("home.views.change_password") as mock_change:
            url = reverse("home:changer_mot_de_passe")
            response = client.post(
                url,
                {
                    "old_password": "",
                    "new_password1": "",
                    "new_password2": "",
                },
                follow=True,
            )

        mock_change.assert_not_called()
        assert response.status_code == 200
        messages = list(get_messages(response.wsgi_request))
        assert any("obligatoires" in str(m).lower() for m in messages)
