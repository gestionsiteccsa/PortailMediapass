"""Configuration des URLs racine du projet Mediapass.

Route ``/admin/`` vers l'administration Django et toutes les autres
routes vers l'application ``home``.
"""
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('home.urls')),
]
