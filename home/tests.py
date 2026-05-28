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


class TestResetPasswordClient:
    """Tests unitaires de reset_password dans pmb_client.py."""

    def test_reset_password_appelle_update_empr(self):
        """Vérifie que reset_password appelle pmbesEmpr_update_empr."""
        from home.services.pmb_client import reset_password

        with patch("home.services.pmb_client.call_pmb") as mock_call:
            mock_call.return_value = {"success": True}
            result = reset_password("12345", "newpass")

        mock_call.assert_called_once_with(
            "pmbesEmpr_update_empr",
            ["12345", {"password": "newpass"}],
        )
        assert result == {"success": True}

    def test_reset_password_propage_erreur(self):
        """Vérifie que PMBClientError est propagée après épuisement des tentatives."""
        from home.services.pmb_client import reset_password

        with patch("home.services.pmb_client.call_pmb") as mock_call:
            mock_call.side_effect = PMBClientError("Erreur PMB")
            with pytest.raises(PMBClientError, match="réinitialiser"):
                reset_password("12345", "newpass")


class TestMotDePasseOublieView:
    """Tests de la vue mot de passe oublié."""

    def test_get_affiche_formulaire(self):
        """GET → 200 + template."""
        url = reverse("home:mot_de_passe_oublie")
        response = Client().get(url)
        assert response.status_code == 200
        assert any("mot_de_passe_oublie" in t.name for t in response.templates)

    def test_post_sans_champs(self):
        """POST sans champs → erreur."""
        url = reverse("home:mot_de_passe_oublie")
        response = Client().post(url, {}, follow=True)
        messages_list = list(get_messages(response.wsgi_request))
        assert any("obligatoires" in str(m) for m in messages_list)

    def test_post_succes_envoie_email(self):
        """POST valide → envoie email + message succès."""
        url = reverse("home:mot_de_passe_oublie")
        response = Client().post(
            url,
            {"card_number": "12345", "email": "user@test.fr"},
            follow=True,
        )
        assert response.status_code == 200
        messages_list = list(get_messages(response.wsgi_request))
        assert any("envoyé" in str(m).lower() for m in messages_list)

    def test_post_securite_cache_existence(self):
        """Le message est le même que la carte existe ou non."""
        url = reverse("home:mot_de_passe_oublie")
        response = Client().post(
            url,
            {"card_number": "99999", "email": "inconnu@test.fr"},
            follow=True,
        )
        messages_list = list(get_messages(response.wsgi_request))
        assert any("envoyé" in str(m).lower() for m in messages_list)


class TestReinitialiserMotDePasseView:
    """Tests de la vue de réinitialisation du mot de passe."""

    def test_token_invalide_redirige(self):
        """Token invalide → redirect + erreur."""
        url = reverse("home:reinitialiser_mot_de_passe", args=["invalide"])
        response = Client().get(url, follow=True)
        assert response.status_code == 200
        messages_list = list(get_messages(response.wsgi_request))
        assert any("invalide" in str(m).lower() for m in messages_list)

    def test_token_valide_affiche_formulaire(self):
        """Token valide → 200 + template."""
        from django.core.signing import TimestampSigner

        token = TimestampSigner().sign("12345:user@test.fr")
        url = reverse("home:reinitialiser_mot_de_passe", args=[token])
        response = Client().get(url)
        assert response.status_code == 200
        assert any("reinitialiser_mot_de_passe" in t.name for t in response.templates)

    def test_post_mots_de_passe_differents(self):
        """POST avec mots de passe différents → erreur."""
        from django.core.signing import TimestampSigner

        token = TimestampSigner().sign("12345:user@test.fr")
        url = reverse("home:reinitialiser_mot_de_passe", args=[token])
        response = Client().post(
            url,
            {"new_password1": "pass1", "new_password2": "pass2"},
            follow=True,
        )
        messages_list = list(get_messages(response.wsgi_request))
        assert any("identiques" in str(m) for m in messages_list)

    def test_post_mot_de_passe_trop_court(self):
        """POST avec mot de passe < 6 caractères → erreur."""
        from django.core.signing import TimestampSigner

        token = TimestampSigner().sign("12345:user@test.fr")
        url = reverse("home:reinitialiser_mot_de_passe", args=[token])
        response = Client().post(
            url,
            {"new_password1": "ab", "new_password2": "ab"},
            follow=True,
        )
        messages_list = list(get_messages(response.wsgi_request))
        assert any("6" in str(m) for m in messages_list)

    def test_post_succes(self):
        """POST valide → appelle reset_password + redirect login."""
        from django.core.signing import TimestampSigner

        token = TimestampSigner().sign("12345:user@test.fr")
        url = reverse("home:reinitialiser_mot_de_passe", args=[token])

        with patch("home.views.reset_password") as mock_reset:
            mock_reset.return_value = {"success": True}
            response = Client().post(
                url,
                {"new_password1": "newpassword", "new_password2": "newpassword"},
                follow=True,
            )

        mock_reset.assert_called_once_with("12345", "newpassword")
        assert response.status_code == 200
        assert response.redirect_chain[-1][0] == reverse("home:login")
        messages_list = list(get_messages(response.wsgi_request))
        assert any("réinitialisé" in str(m).lower() for m in messages_list)

    def test_post_erreur_pmb(self):
        """POST avec échec PMB → message d'erreur."""
        from django.core.signing import TimestampSigner

        token = TimestampSigner().sign("12345:user@test.fr")
        url = reverse("home:reinitialiser_mot_de_passe", args=[token])

        with patch("home.views.reset_password") as mock_reset:
            mock_reset.side_effect = PMBClientError("Erreur PMB")
            response = Client().post(
                url,
                {"new_password1": "newpassword", "new_password2": "newpassword"},
                follow=True,
            )

        assert response.status_code == 200
        messages_list = list(get_messages(response.wsgi_request))
        assert any("échoué" in str(m).lower() for m in messages_list)
