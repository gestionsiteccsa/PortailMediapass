# Checklist SOLID pour Pull Requests

Utilisez cette checklist lors de chaque PR pour garantir le respect des principes SOLID.

---

## S — Single Responsibility

- [ ] La vue contient-elle uniquement du code HTTP (pas de logique métier) ?
- [ ] Le modèle contient-il uniquement les règles métier (pas d'effets de bord) ?
- [ ] Les use cases orchestrent-ils sans faire de logique métier ?
- [ ] Chaque classe a-t-elle **une seule raison de changer** ?
- [ ] Les services d'infrastructure (email, paiement) sont-ils séparés du métier ?

## O — Open/Closed

- [ ] Une nouvelle fonctionnalité ajoute-t-elle des fichiers sans modifier l'existant ?
- [ ] Les interfaces sont-elles stables (peu de changements après fusion) ?
- [ ] Le Strategy/Adapter pattern est-il utilisé pour les comportements variables ?
- [ ] Aucun `if` / `match` sur des types de stratégies métier ?

## L — Liskov Substitution

- [ ] Les sous-classes respectent-elles le contrat de l'interface parente ?
- [ ] Les exceptions sont-elles spécialisées et prévues par l'interface ?
- [ ] Les pré/post-conditions sont-elles documentées et respectées ?
- [ ] Aucun `raise NotImplementedError` dans une sous-classe concrète ?

## I — Interface Segregation

- [ ] Les interfaces ont-elles **3 méthodes ou moins** en moyenne ?
- [ ] Aucune classe n'implémente de méthode vide ou `pass` ?
- [ ] Les interfaces sont-elles spécifiques à un seul usage ?
- [ ] Aucune interface nommée `I...Service` qui regroupe tout ?

## D — Dependency Inversion

- [ ] Les dépendances des modules de haut niveau pointent-elles vers des abstractions ?
- [ ] Les modules de bas niveau (infrastructure) implémentent-ils des interfaces ?
- [ ] Pas d'import direct de `models.py` dans les services/use cases ?
- [ ] Les dépendances sont-elles injectées (constructeur ou paramètre) ?
- [ ] Les tests peuvent-ils remplacer n'importe quelle dépendance par un mock ?

## Architecture générale

- [ ] La couche `domain/` ne dépend d'**aucune** autre couche
- [ ] La couche `application/` dépend uniquement de `domain/`
- [ ] La couche `infrastructure/` dépend uniquement de `domain/`
- [ ] La couche `presentation/` dépend de `application/` et `infrastructure/`
- [ ] Les imports suivent la hiérarchie (pas de remontée)

## Tests

- [ ] Nouveaux use cases testés unitairement
- [ ] Mocks utilisés pour isoler les dépendances
- [ ] Cas d'erreur testés (exceptions métier)
- [ ] Tests des repositories en intégration (pytest-django)

## Code quality

- [ ] Pas de logique métier dans les serializers DRF
- [ ] Pas de `print()` de debug
- [ ] Pas de `.get()` sans gestion d'erreur
- [ ] Typage Python strict (type hints partout)
- [ ] Dataclasses utilisées pour les DTOs et value objects
