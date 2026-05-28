# API PMB — Connecteur JSON-RPC `api_recherche` (source_id=4)

Tous les appels sont effectués via une requête POST JSON-RPC vers :
```
https://fourmies.pmbpro.net/ws/connector_out.php?source_id=4
```

---

## pmbesSearch — Fonctions pour effectuer des recherches dans le catalogue

| Méthode | Description | Statut |
|---|---|---|
| `simpleSearch` | Effectuer une recherche simple | ✅ Fonctionne |
| `simpleSearchLocalise` | Recherche simple filtrée par localisation et section | ❓ Non testé |
| `getAdvancedSearchFields` | Récupérer la liste des champs recherchables en recherche avancée | ❓ Non testé |
| `getAdvancedSearchField` | Récupérer les informations d'un champ de recherche | ❓ Non testé |
| `advancedSearch` | Effectuer une recherche avancée | ❓ Non testé |
| `get_sort_types` | Renvoie la liste des différents tris possibles | ❓ Non testé |
| `fetchSearchRecords` | Récupérer les notices issues d'une recherche | ✅ Fonctionne (retourne ID uniquement) |
| `fetchSearchRecordsSorted` | Récupérer les notices triées issues d'une recherche | ✅ Fonctionne |
| `fetchSearchRecordsArray` | Récupérer les notices issues d'une recherche | ❌ Réponse vide |
| `fetchSearchRecordsArraySorted` | Récupérer les notices triées issues d'une recherche | ❌ Non testé |
| `fetchSearchRecordsFull` | Récupérer les notices complètes issues d'une recherche | ❌ Réponse vide |
| `fetchSearchRecordsFullSorted` | Récupérer les notices complètes triées | ❌ Non testé |
| `fetchSearchRecordsFullWithBullId` | Récupérer les notices complètes avec ID bulletin | ❌ Non testé |
| `fetchSearchRecordsFullWithBullIdSorted` | Récupérer les notices complètes triées avec ID bulletin | ❌ Non testé |
| `listExternalSources` | — | ❌ Non testé |
| `listFacets` | Récupérer les facettes issues d'une recherche | ❓ Non testé |
| `listRecordsFromFacets` | Récupérer les notices issues d'une ou plusieurs facettes | ❓ Non testé |

---

## pmbesItems — Fonctions relatives aux exemplaires

| Méthode | Description | Statut |
|---|---|---|
| `fetch_notice_items` | Renvoie les exemplaires associés à une notice | ✅ Fonctionne |
| `fetch_notices_items` | Renvoie les exemplaires associés à une liste de notices | ❌ 500 |
| `fetch_bulletins_items` | Renvoie les exemplaires associés à une liste de bulletins | ❓ Non testé |
| `fetch_item` | Renvoie un exemplaire à partir de l'un de ses identifiants | ✅ Fonctionne (vide) |
| `fetch_item_info` | Renvoie un exemplaire à partir de l'un de ses identifiants | ✅ Fonctionne (vide) |

---

## pmbesNotices — Fonctions relatives aux notices

| Méthode | Description | Statut |
|---|---|---|
| `fetchNoticeList` | Récupère une liste de notices à partir de leurs IDs | ✅ Fonctionne (ID uniquement) |
| `fetchExternalNoticeList` | — | ✅ Fonctionne (ID uniquement) |
| `fetchNoticeListArray` | Notices sous forme de tableau UNIMARC | ❌ Réponse vide |
| `listNoticeExplNums` | Liste les documents numériques associés à une notice | ✅ Fonctionne (vide) |
| `listNoticesExplNums` | Idem pour plusieurs notices | ❓ Non testé |
| `listBulletinExplNums` | Liste les documents numériques associés à un bulletin | ❓ Non testé |
| `listBulletinsExplNums` | Idem pour plusieurs bulletins | ❓ Non testé |
| `fetchNoticeByExplCb` | Récupérer une notice par code-barres exemplaire | ❌ 500 |
| `fetch_notices_bulletins` | Retourne les bulletins associés à des notices de périodique | ❓ Non testé |
| `fetchNoticeListFull` | Renvoie le plus d'informations possible sur une série de notices | ✅ Fonctionne (ID + items + admin) |
| `fetch_bulletin_list` | Renvoie une liste de bulletins | ❓ Non testé |
| `findNoticeBulletinId` | — | ❓ Non testé |
| `fetchBulletinListFull` | Renvoie le plus d'informations sur une série de bulletins | ✅ Fonctionne (vide) |
| `fetchNoticesCollstates` | — | ❌ 500 |
| `fetchSerialList` | — | ❓ Non testé |
| `fetchNoticeListFullWithBullId` | Renvoie le plus d'informations sur une série de notices (avec ID bulletin) | ✅ Fonctionne (comme Full) |
| `fetchNoticesBulletinsList` | Renvoie une liste de bulletins | ✅ Fonctionne (vide) |
| `fetchNoticesAdministrative` | Renvoie les informations de gestion d'une notice | ❌ 500 |
| `deleteNotices` | Supprime la liste des notices | ❌ Non testé (destructeur) |
| `checkdelnotice` | Vérifie que la notice peut être supprimée | ❌ Non testé |

---

## pmbesOPACEmpr — Interactions OPAC côté emprunteur

| Méthode | Description | Statut |
|---|---|---|
| `login` | Authentifie un lecteur, renvoie un numéro de session | ✅ Fonctionne |
| `login_md5` | Authentifie un lecteur (MD5) | ❌ Retourne 0 (non supporté) |
| `login_aes` | Authentifie un lecteur (AES) | ❌ Retourne 0 (non supporté) |
| `login_token` | Authentifie un lecteur avec token chiffré | ❓ Non testé |
| `logout` | Invalide un numéro de session | ✅ Fonctionne |
| `list_locations` | Liste les différentes localisations de l'OPAC | ❓ Non testé |
| `get_account_info` | Retrouve les informations du compte du lecteur | ✅ Fonctionne |
| `change_password` | Change le mot de passe de l'emprunteur | ❓ Non testé |
| `list_loans` | Retrouve les différents prêts d'un emprunteur | ✅ Fonctionne (vide si aucun) |
| `list_resas` | Liste les réservations associées à un emprunteur | ✅ Fonctionne (vide si aucune) |
| `delete_resa` | — | ❓ Non testé |
| `add_review` | Ajoute un avis sur une notice | ❓ Non testé |
| `add_tag` | Ajoute un tag sur une notice | ❓ Non testé |
| `list_suggestion_categories` | Renvoie les différentes catégories disponibles pour les suggestions | ❓ Non testé |
| `list_suggestion_sources` | — | ❓ Non testé |
| `list_suggestion_sources_and_categories` | — | ❓ Non testé |
| `add_suggestion` | Soumet une suggestion | ❓ Non testé |
| `add_suggestion2` | — | ❓ Non testé |
| `edit_suggestion` | — | ❓ Non testé |
| `delete_suggestion` | — | ❓ Non testé |
| `list_suggestions` | Liste les suggestions associées à un emprunteur | ❓ Non testé |
| `list_resa_locations` | Renvoie les différentes localisations disponibles pour une réservation | ❓ Non testé |
| `can_reserve_notice` | — | ❓ Non testé |
| `add_resa` | Ajoute une réservation pour une notice | ❓ Non testé |
| `list_abonnements` | Liste les différents abonnements du lecteur | ❓ Non testé |
| `list_cart_content` | Liste le contenu du panier d'un emprunteur | ❓ Non testé |
| `add_notices_to_cart` | Ajoute des notices au panier d'un emprunteur | ❓ Non testé |
| `delete_notices_from_cart` | Enlève des notices du panier d'un emprunteur | ❓ Non testé |
| `empty_cart` | Vide le panier d'un emprunteur | ❓ Non testé |
| `list_shelves` | Liste les étagères | ❓ Non testé |
| `retrieve_shelf_content` | Liste les notices contenues dans une étagère | ❓ Non testé |
| `self_checkout` | Permet de faire le prêt d'un document | ❓ Non testé |
| `self_checkin` | Permet de faire le retour d'un document | ❓ Non testé |
| `self_renew` | Permet de faire la prolongation de prêt d'un document | ❓ Non testé |
| `get_author_information_and_notices` | Combine auteur + ses notices | ❓ Non testé |
| `get_collection_information_and_notices` | — | ❓ Non testé |
| `get_subcollection_information_and_notices` | — | ❓ Non testé |
| `get_publisher_information_and_notices` | — | ❓ Non testé |
| `list_thesauri` | — | ❓ Non testé |
| `fetch_thesaurus_node_full` | — | ❓ Non testé |
| `fetchSearchRecordsFull` | Récupérer les notices complètes | ❓ Non testé (via anonymous) |
| `getReadingLists` | — | ❓ Non testé |
| `getPublicReadingLists` | — | ❓ Non testé |
| `addNoticesToReadingList` | — | ❓ Non testé |
| `removeNoticesFromReadingList` | — | ❓ Non testé |
| `emptyReadingList` | — | ❓ Non testé |
| `listFacets` | Récupérer les facettes | ❓ Non testé |
| `listRecordsFromFacets` | Récupérer les notices issues de facettes | ❓ Non testé |
| `checkExternalAuthentication` | Teste l'utilisation d'une connexion externe | ❓ Non testé |

---

## pmbesOPACAnonymous — Interactions OPAC côté anonyme

| Méthode | Description | Statut |
|---|---|---|
| `simpleSearch` | Effectuer une recherche simple | ❓ Non testé (alias) |
| `fetchSearchRecords` | Récupérer les notices issues d'une recherche | ❓ Non testé (alias) |
| `fetchSearchRecordsFull` | Récupérer les notices complètes | ❓ Non testé |
| `fetchNoticeList` | Récupère une liste de notices | ❓ Non testé (alias) |
| `fetchNoticeListArray` | Récupère une liste de notices (UNIMARC) | ❓ Non testé (alias) |
| `fetchNoticeListFull` | Alias de `pmbesNotices_fetchNoticeListFull` | ❓ Non testé |
| `fetch_notice_items` | Renvoie les exemplaires associés à une notice | ❓ Non testé |
| `list_shelves` | Liste les étagères | ❓ Non testé |
| `retrieve_shelf_content` | Liste les notices d'une étagère | ❓ Non testé |
| `get_author_information_and_notices` | Info auteur + notices | ❓ Non testé |
| `get_collection_information_and_notices` | Info collection + notices | ❓ Non testé |
| `get_publisher_information_and_notices` | Info éditeur + notices | ❓ Non testé |
| *Toutes les autres fonctions* | Identiques à pmbesNotices/pmbesSearch | ❓ Non testé |

---

## pmbesOPACGeneric — Fonctions OPAC (anonyme + connecté)

| Méthode | Description | Statut |
|---|---|---|
| `list_shelves` | Liste les étagères | ❓ Non testé |
| `retrieve_shelf_content` | Liste les notices contenues dans une étagère | ❓ Non testé |
| `list_locations` | Liste les différentes localisations de l'OPAC | ❓ Non testé |
| `get_location_information` | Renvoie les informations associées à une localisation | ❓ Non testé |
| `get_location_information_and_sections` | Location + sections associées | ❓ Non testé |
| `list_sections` | Liste les sections visibles de l'OPAC | ❓ Non testé |
| `get_section_information` | Renvoie les informations associées à une section | ❓ Non testé |
| `get_all_locations_and_sections` | Toutes les localisations + sections | ✅ Fonctionne |
| `is_also_borrowed_enabled` | Savoir si "Autre Lecture" est activée | ❓ Non testé |
| `also_borrowed` | Renvoie les autres lectures associées à une notice | ✅ Fonctionne (vide) |
| `get_infopage` | — | ❓ Non testé |
| `get_marc_table` | Récupère les infos des fichiers XML de paramétrage PMB | ❓ Non testé |
| `selector` | Fonctions de sélection | ✅ Fonctionne (vide) |

---

## pmbesAuthors — Fonctions relatives aux auteurs

| Méthode | Description | Statut |
|---|---|---|
| `get_author_information` | Renvoie les informations d'un auteur à partir de son ID | ❓ Non testé |
| `list_author_notices` | Liste les notices d'un auteur | ❓ Non testé |
| `get_author_information_and_notices` | Combine auteur + notices | ❓ Non testé |

---

## pmbesPublishers — Fonctions relatives aux éditeurs

| Méthode | Description | Statut |
|---|---|---|
| `get_publisher_information` | Renvoie les informations relatives à un éditeur | ❓ Non testé |
| `list_publisher_notices` | Renvoie les IDs des notices associées à un éditeur | ❓ Non testé |
| `get_publisher_information_and_notices` | Éditeur + notices associées | ❓ Non testé |

---

## pmbesCollections — Fonctions relatives aux collections

| Méthode | Description | Statut |
|---|---|---|
| `get_collection_information` | Renvoie les informations d'une collection | ❓ Non testé |
| `get_subcollection_information` | Renvoie les informations d'une sous-collection | ❓ Non testé |
| `list_collection_notices` | Renvoie les IDs des notices d'une collection | ❓ Non testé |
| `list_collection_subcollections` | Liste les sous-collections d'une collection | ❓ Non testé |
| `list_subcollection_notices` | Renvoie les IDs des notices d'une sous-collection | ❓ Non testé |
| `get_collection_information_and_notices` | Collection + notices | ❓ Non testé |
| `get_subcollection_information_and_notices` | Sous-collection + notices | ❓ Non testé |

---

## pmbesSelfServices — Prêt/retour/prolongation libre-service

| Méthode | Description | Statut |
|---|---|---|
| `self_checkout` | Permet de faire le prêt d'un document | ❓ Non testé |
| `self_del_temp_pret` | Permet de supprimer le prêt temporaire | ❓ Non testé |
| `self_checkin` | Permet de faire le retour d'un document | ❓ Non testé |
| `self_renew` | Permet de faire la prolongation de prêt | ❓ Non testé |
| `self_checkout_bibloto` | Prêt via l'application Bibloto | ❓ Non testé |
| `get_loans_printer_template` | Template d'impression d'un ticket de prêt | ❓ Non testé |
| `get_printers_config` | Valeurs des paramètres de configuration des imprimantes | ❓ Non testé |

---

## pmbesConvertImport — Conversion et import de notices

| Méthode | Description | Statut |
|---|---|---|
| `get_convert_types` | Liste des types de conversions possibles | ✅ Fonctionne (49 types) |
| `convert` | Convertit une notice d'un format vers un autre | ❌ 500 |
| `convert_by_path` | Convertit une notice (utilisation du chemin du type) | ❌ Pas de données |
| `import` | Import Z39.50 de notice | ❓ Non testé |
| `import_basic` | Import de notices (équivalent admin PMB) | ❓ Non testé |

---

## pmbesEmpr — Fonctions relatives au lecteur

| Méthode | Description | Statut |
|---|---|---|
| `fetch_empr` | Renvoie les informations d'un lecteur par ID | ❓ Non testé |
| `delete_empr` | Suppression d'un lecteur | ❌ Non testé (destructeur) |
| `create_empr` | Création d'un lecteur | ❓ Non testé |
| `update_empr` | Modification d'un lecteur | ❓ Non testé |
| `empr_list` | Liste de lecteurs | ❓ Non testé |
| `statut_list` | Liste des statuts de lecteur | ❓ Non testé |
| `categ_list` | Liste des catégories de lecteur | ❓ Non testé |
| `codestat_list` | Liste des codes statistiques de lecteur | ❓ Non testé |
| `lang_list` | Liste des codes de langue | ❓ Non testé |
| `groupe_list` | Liste des groupes de lecteurs | ❓ Non testé |
| `abt_list` | Liste des types d'abonnement | ❓ Non testé |
| `location_list` | Liste des localisations | ❓ Non testé |
| `surlocation_list` | Liste des sur-localisations | ❓ Non testé |
| `caddie_list` | Liste des paniers de lecteur | ❓ Non testé |
| `caddie_empr_list` | Liste des lecteurs d'un panier | ❓ Non testé |
| `add_in_caddie` | — | ❓ Non testé |
| `pointe_in_caddie` | — | ❓ Non testé |
| `is_in_caddie` | Présence dans un panier | ❓ Non testé |
| `caddie_pointage_raz` | Raz des pointages d'un panier | ❓ Non testé |
| `pperso_list_type_values` | Liste des valeurs d'un champ personnalisé de type liste | ❓ Non testé |
| `bibloto_empr_list` | Liste de lecteurs pour Bibloto | ❓ Non testé |
| `send_mail_pret_info_to_empr` | Envoi de mail | ❓ Non testé |

---

## pmbesDatabase — Gestion de la base de données PMB

| Méthode | Description | Statut |
|---|---|---|
| `get_version_informations` | Donne les informations sur la version de PMB | ❓ Non testé |
| `need_update` | La base a-t-elle besoin d'une mise à jour | ❓ Non testé |
| `update` | Fonction de mise à jour de la base de données | ❌ Non testé (destructeur) |
| `is_utf8` | Le logiciel est-il configuré en UTF-8 | ❓ Non testé |
| `convert_to_utf8` | Conversion de la base en UTF-8 | ❌ Non testé (destructeur) |

---

## pmbesAI — Intelligence artificielle

| Méthode | Description | Statut |
|---|---|---|
| `getDocnumsContent` | Retourne un tableau du contenu des documents numériques | ❓ Non testé |
| `getSummariesContent` | Retourne un tableau du résumé des notices | ❓ Non testé |

---

## Autres groupes (non testés)

| Groupe | Description |
|---|---|
| `pmbesRepositories` | Gestion des entrepôts du connecteur agnostique |
| `pmbesThesauri` | Fonctions relatives aux thésaurus |
| `pmbesAutLinks` | Liens entre les autorités |
| `pmbesTasks` | Planificateur de tâches |
| `pmbesDSI` | Diffusion sélective d'informations |
| `pmbesBackup` | Sauvegarde |
| `pmbesSync` | Synchronisation des entrepôts |
| `pmbesClean` | Nettoyage et indexation |
| `pmbesOPACStats` | Statistiques OPAC |
| `pmbesMySQL` | Opérations MySQL |
| `pmbesProcs` | Procédures |
| `pmbesCommons` | Utilitaires (UNIMARC labels) |
| `pmbesMailing` | Mailing |
| `pmbesIndex` | Indexation |
| `pmbesScanDocnum` | Documents numériques |
| `pmbesDocwatches` | Veilles documentaires |
| `pmbesCairn` | Connecteur Cairn.info |
| `pmbesContributions` | Connecteur de contributions |
| `pmbesChklnk` | Vérification de liens |
| `pmbesPNB` | Prêt numérique |
| `pmbesAccessRights` | Droits d'accès |

---

## Résumé des fonctions testées

| Statut | Signification |
|---|---|
| ✅ Fonctionne | La fonction retourne des données exploitables |
| ❌ 500 / Réponse vide | La fonction existe mais ne retourne rien d'utile |
| ❓ Non testé | Fonction disponible mais pas encore testée |
| ❌ Destructeur | Fonction à risque (suppression, modification) |

### Fonctionnel actuellement dans le catalogue :
- `pmbesSearch_simpleSearch` → recherche
- `pmbesSearch_fetchSearchRecords` → liste des IDs
- `pmbesNotices_fetchNoticeListFull` → exemplaires + données admin
- `pmbesItems_fetch_notice_items` → exemplaires

### Limitation principale :
**Aucune fonction ne retourne le titre, l'auteur, l'éditeur ou le résumé des notices.**

### Test SOAP (source_id=3) :
Le connecteur SOAP `api_recherche_soap` (source_id=3) a été testé :
- Retourne une réponse vide pour tous les types d'appels (JSON-RPC et SOAP XML)
- Le WSDL est accessible (73KB, 27 méthodes) mais les appels ne produisent aucune réponse
- **Le connecteur SOAP n'est pas fonctionnel**

### Pour obtenir les titres, solutions possibles :
1. Contacter l'hébergeur (reseaubibli.fr) pour demander l'activation d'un connecteur JSON-RPC complet incluant `pmbesNotices_getNotice`
2. Demander la réparation du connecteur SOAP `api_recherche_soap` (source_id=3)
3. Scraper l'interface OPAC publique (non recommandé)
