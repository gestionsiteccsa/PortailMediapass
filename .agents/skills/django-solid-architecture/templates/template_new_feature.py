"""Template pour créer une nouvelle feature Django avec architecture SOLID.

Utilisation :
1. Copier ce fichier dans votre app : apps/<app_name>/new_feature.py
2. Suivre les étapes marquées "TODO"
3. Supprimer ce commentaire d'en-tête

Étapes :
  1. Définir le domaine (entités, interfaces, exceptions)
  2. Créer les use cases
  3. Implémenter l'infrastructure (repositories, adapters)
  4. Créer la présentation (views, serializers)
  5. Câbler les dépendances (wiring)
  6. Écrire les tests
"""

from __future__ import annotations

# =============================================================================
# ÉTAPE 1 : DOMAIN
# =============================================================================

# --- domain/models.py -------------------------------------------------------
"""
TODO : Définir les entités du domaine avec @dataclass

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID, uuid4


@dataclass
class <EntityName>:
    id: Optional[UUID] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @property
    def <computed_property>(self) -> str:
        ...
"""

# --- domain/value_objects.py ------------------------------------------------
"""
TODO : Définir les value objects immutables

from dataclasses import dataclass


@dataclass(frozen=True)
class <ValueObject>:
    ...

    def __post_init__(self) -> None:
        if not self._is_valid():
            raise ValueError("Validation failed")
"""

# --- domain/interfaces.py ---------------------------------------------------
"""
TODO : Définir les interfaces (repositories, services)

from abc import ABC, abstractmethod
from uuid import UUID

from .models import <EntityName>


class I<Entity>Repository(ABC):
    @abstractmethod
    def save(self, entity: <EntityName>) -> <EntityName>: ...

    @abstractmethod
    def get_by_id(self, entity_id: UUID) -> <EntityName>: ...

    @abstractmethod
    def find_all(self) -> list[<EntityName>]: ...


class I<ExternalService>(ABC):
    @abstractmethod
    def execute(self, entity: <EntityName>) -> <Result>: ...
"""

# --- domain/exceptions.py ---------------------------------------------------
"""
TODO : Définir les exceptions métier

from uuid import UUID


class <Domain>Error(Exception):
    """Erreur de base du domaine."""


class <Entity>NotFoundError(<Domain>Error):
    def __init__(self, entity_id: UUID):
        self.entity_id = entity_id
        super().__init__(f"Entité {entity_id} introuvable")


class <BusinessRule>Error(<Domain>Error):
    def __init__(self, message: str):
        super().__init__(message)
"""

# =============================================================================
# ÉTAPE 2 : APPLICATION
# =============================================================================

# --- application/dto.py -----------------------------------------------------
"""
TODO : Définir les DTOs pour les entrées/sorties des use cases

from dataclasses import dataclass
from uuid import UUID


@dataclass
class Create<Entity>Request:
    ...


@dataclass
class <Entity>Response:
    id: UUID
    ...
"""

# --- application/use_cases.py -----------------------------------------------
"""
TODO : Créer les use cases (orchestration, pas de logique métier)

from __future__ import annotations

from ..domain.interfaces import I<Entity>Repository, I<ExternalService>
from ..domain.models import <EntityName>
from .dto import Create<Entity>Request, <Entity>Response


class Create<Entity>UseCase:
    def __init__(
        self,
        repo: I<Entity>Repository,
        service: I<ExternalService>,
    ):
        self._repo = repo
        self._service = service

    def execute(self, request: Create<Entity>Request) -> <EntityName>:
        # 1. Créer l'entité
        entity = <EntityName>(...)

        # 2. Valider (déléguer aux méthodes de l'entité)
        # entity.validate()

        # 3. Persister
        saved = self._repo.save(entity)

        # 4. Effets de bord (email, notification, etc.)
        self._service.execute(saved)

        return saved
"""

# =============================================================================
# ÉTAPE 3 : INFRASTRUCTURE
# =============================================================================

# --- infrastructure/repositories.py -----------------------------------------
"""
TODO : Implémenter les repositories concrets

from uuid import UUID

from django.shortcuts import get_object_or_404

from ..domain.interfaces import I<Entity>Repository
from ..domain.models import <EntityName>


class Django<Entity>Repository(I<Entity>Repository):
    def save(self, entity: <EntityName>) -> <EntityName>:
        from ..models import <Entity>Model

        if entity.id:
            obj = <Entity>Model.objects.get(pk=entity.id)
            # Mettre à jour les champs
            obj.save()
        else:
            obj = <Entity>Model.objects.create(...)

        return self._to_domain(obj)

    def get_by_id(self, entity_id: UUID) -> <EntityName>:
        from ..models import <Entity>Model

        obj = get_object_or_404(<Entity>Model, pk=entity_id)
        return self._to_domain(obj)

    @staticmethod
    def _to_domain(obj) -> <EntityName>:
        return <EntityName>(
            id=obj.id,
            ...
        )
"""

# --- infrastructure/adapters.py ---------------------------------------------
"""
TODO : Implémenter les adapters concrets

from django.conf import settings
from django.core.mail import send_mail

from ..domain.interfaces import I<ExternalService>
from ..domain.models import <EntityName>


class Django<ExternalService>(I<ExternalService>):
    def execute(self, entity: <EntityName>) -> None:
        ...
"""

# --- infrastructure/models.py (si nécessaire) --------------------------------
"""
TODO : Définir les modèles Django ORM

import uuid
from django.db import models


class <Entity>Model(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = "<app_name>"
        db_table = "<app_name>_<entity>"
"""

# =============================================================================
# ÉTAPE 4 : PRÉSENTATION
# =============================================================================

# --- presentation/views.py --------------------------------------------------
"""
TODO : Créer les vues

from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect, render
from django.views import View

from ..application.dto import Create<Entity>Request
from ..application.use_cases import Create<Entity>UseCase
from ..domain.exceptions import <Domain>Error


class <Entity>CreateView(LoginRequiredMixin, View):
    def __init__(self, use_case: Create<Entity>UseCase, **kwargs):
        super().__init__(**kwargs)
        self._use_case = use_case

    def get(self, request):
        return render(request, "<app_name>/<entity>_form.html")

    def post(self, request):
        try:
            request_dto = Create<Entity>Request(...)
            entity = self._use_case.execute(request_dto)
            return redirect("<entity>_detail", pk=entity.id)
        except <Domain>Error as e:
            return render(
                request,
                "<app_name>/<entity>_form.html",
                {"error": str(e)},
                status=400,
            )
"""

# --- presentation/urls.py ---------------------------------------------------
"""
TODO : Définir les URLs

from django.urls import path

urlpatterns = [
    path("<entities>/create/", <Entity>CreateView.as_view(), name="<entity>_create"),
    path("<entities>/<uuid:pk>/", <Entity>DetailView.as_view(), name="<entity>_detail"),
]
"""

# =============================================================================
# ÉTAPE 5 : WIRING (config/urls.py)
# =============================================================================

"""
TODO : Câbler les dépendances

from <app>.infrastructure.repositories import Django<Entity>Repository
from <app>.infrastructure.adapters import Django<ExternalService>
from <app>.application.use_cases import Create<Entity>UseCase
from <app>.presentation.views import <Entity>CreateView

repo = Django<Entity>Repository()
service = Django<ExternalService>()
use_case = Create<Entity>UseCase(repo=repo, service=service)

urlpatterns = [
    path("<entities>/create/", <Entity>CreateView.as_view(use_case=use_case), name="<entity>_create"),
]
"""

# =============================================================================
# ÉTAPE 6 : TESTS
# =============================================================================

"""
TODO : Écrire les tests unitaires et d'intégration

--- tests/test_use_cases.py ---
from unittest.mock import MagicMock
import pytest
from uuid import uuid4

from <app>.application.use_cases import Create<Entity>UseCase


class TestCreate<Entity>UseCase:
    @pytest.fixture
    def mock_repo(self):
        return MagicMock()

    @pytest.fixture
    def mock_service(self):
        return MagicMock()

    @pytest.fixture
    def use_case(self, mock_repo, mock_service):
        return Create<Entity>UseCase(repo=mock_repo, service=mock_service)

    def test_create_success(self, use_case, mock_repo, mock_service):
        request = Create<Entity>Request(...)
        result = use_case.execute(request)
        mock_repo.save.assert_called_once()
        mock_service.execute.assert_called_once()

    def test_create_failure(self, use_case, mock_repo):
        ...


--- tests/test_repositories.py ---
@pytest.mark.django_db
class TestDjango<Entity>Repository:
    def setup_method(self):
        self.repo = Django<Entity>Repository()

    def test_save_and_retrieve(self):
        entity = <EntityName>(...)
        saved = self.repo.save(entity)
        retrieved = self.repo.get_by_id(saved.id)
        assert retrieved.id == saved.id
        ...
"""
