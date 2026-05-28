# Mediapass

Portail web intercommunal de bibliothèque, interface grand public du système PMB
(PhpMyBibli) via son API JSON-RPC.

## Objectif

Mediapass permet aux usagers des bibliothèques du réseau de :

-   Rechercher des documents dans le catalogue collectif
-   Consulter les détails d'une notice (auteur, résumé, disponibilité)
-   Se connecter à leur compte lecteur
-   Visualiser leurs prêts en cours, réservations et historique
-   Effectuer des réservations et prolonger des prêts

## Stack technique

| Technologie       | Usage                                     |
| ----------------- | ----------------------------------------- |
| **Django 6.0.5**  | Framework web (pas de DRF, vues fonctionnelles) |
| **Python 3.12**   | Langage                                   |
| **SQLite**        | Base de données (sessions/auth uniquement) |
| **Tailwind CSS 3**| UI via CDN (pas de build npm)             |
| **PMB API**       | JSON-RPC avec certificat client PKCS#12   |

## Conventions

-   Code et documentation en **français**
-   Vues **fonctionnelles** uniquement (pas de `class-based views`)
-   Pas de modèles Django personnalisés (les données viennent de PMB)
-   Documentation auto-générée via `mkdocstrings` à partir des docstrings Google

## Dépendances principales

-   `Django>=6.0,<6.1`
-   `requests>=2.32,<3`
-   `cryptography>=44,<49`
-   `python-dotenv>=1.0,<2`

Voir le fichier `requirements.txt` pour la liste complète.
