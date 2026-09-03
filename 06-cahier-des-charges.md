# 06 - Cahier des charges

## Projet

**Nom :** JobMarket Data Platform
**Auteur :** Abdarrazzak HOUTI
**Périmètre :** analyse des offres d'emploi data en France
**Version :** MVP local soutenable - septembre 2026
**Moteur de transformation :** PySpark
**Stockage analytique :** PostgreSQL, schéma `analytics`

## 1. Objectifs et besoins

JobMarket Data Platform est un projet de Data Engineering visant à collecter, traiter, stocker et valoriser des offres d'emploi data en France.

L'objectif principal est de fournir une vision fiable du marché : métiers demandés, compétences techniques, entreprises qui recrutent, villes les plus actives, niveaux de salaire lorsque l'information est disponible, et recommandations d'offres selon un profil candidat.

### Problématiques

- Les offres sont dispersées entre plusieurs job boards et APIs.
- Les intitulés, localisations, entreprises et salaires ne sont pas normalisés.
- Les descriptions renvoyées par certaines APIs peuvent être tronquées, ce qui réduit la qualité de l'extraction des compétences.
- Les tableaux de bord doivent rester lisibles pour un utilisateur non technique.
- La base finale ne doit contenir ni fausses offres, ni URLs d'exemple, ni données de démonstration.

### Valeur ajoutée

- Centraliser des offres réelles spécialisées data en France.
- Construire un pipeline reproductible avec PySpark et une architecture Bronze, Silver, Gold.
- Enrichir les descriptions depuis les liens Adzuna stockés afin de mieux détecter les technologies.
- Fournir une API et un dashboard pour explorer le marché sans manipuler la base directement.
- Préparer une trajectoire cloud Azure compatible avec un contexte professionnel.

## 2. Fonctionnalités principales

### Données à collecter

Le périmètre cible concerne les offres data en France : Data Analyst, Data Engineer, Data Scientist, BI Analyst, Analytics Engineer, Machine Learning Engineer et postes proches.

La source principale opérationnelle est l'API Adzuna. Le connecteur The Muse et le web scraping restent prévus comme extensions, sous réserve des conditions d'utilisation des sites.

- **Adzuna API :** collecte principale des offres réelles France.
- **Scraping Adzuna :** récupération des descriptions HTML complètes depuis les liens stockés en base.
- **The Muse API :** connecteur complémentaire prévu pour enrichir le corpus lorsque les données sont pertinentes.
- **Web scraping optionnel :** Welcome to the Jungle ou HelloWork uniquement si le cadre légal, `robots.txt` et les conditions d'utilisation l'autorisent.

### Marché de l'emploi

Le dashboard doit permettre d'identifier les villes qui recrutent le plus, les compétences les plus demandées, les entreprises présentes dans le corpus et la répartition des offres.

Les localisations doivent être nettoyées afin d'afficher des villes françaises lisibles, et non des libellés administratifs comme des arrondissements ou des chaînes trop longues.

### Recommandations d'emplois personnalisées

La solution doit générer des recommandations simples et explicables à partir des compétences, du métier recherché, de la localisation et du niveau d'information disponible dans les offres.

La première version privilégie une logique transparente plutôt qu'un modèle opaque.

### Recherche interactive

Le dashboard doit proposer un moteur de recherche multicritère permettant de filtrer les offres par mot-clé, ville, compétences, type de contrat, expérience, source et salaire minimum.

### Analytique salaire optionnelle

La solution peut préparer des vues dédiées à l'analyse et à une éventuelle prédiction de salaires. Cette partie n'est pas une obligation IA du projet : elle sert à montrer que le pipeline produit des données suffisamment structurées pour une évolution analytique.

### Monitoring et alertes

Le projet doit exposer un suivi de disponibilité et de qualité via Prometheus et Grafana. Une page Monitoring doit aussi être visible dans Streamlit pour la démonstration.

Les alertes mail doivent fonctionner en mode prévisualisation. L'envoi réel est activé uniquement si une configuration SMTP est fournie.

### Automatisation Airflow

La collecte et les traitements doivent pouvoir être automatisés par Airflow. La fréquence doit être configurable afin de permettre une exécution quotidienne ou hebdomadaire sans modifier le code.

### Qualité et traçabilité

- Conserver la source de chaque offre.
- Supprimer les doublons sur les identifiants d'offres.
- Produire un rapport qualité.
- Ne pas exposer les identifiants techniques dans l'interface utilisateur.
- Documenter les limites connues : quotas API, descriptions tronquées, disponibilité des salaires.

## 3. Contraintes techniques

### Collecte

Les extracteurs doivent récupérer des données réelles et refuser les jeux d'exemple dans la base finale.

Les secrets API sont stockés dans un fichier local `.env`, non versionné. Les erreurs de collecte doivent être visibles afin d'éviter de masquer un problème par de fausses données.

Les logs ne doivent pas afficher de clés API, mots de passe ou jetons. Un contrôle avant publication doit vérifier que les valeurs sensibles du `.env` ne sont pas présentes dans les fichiers du projet.

### Stockage et traitement

- **Bronze :** fichiers JSON bruts par source.
- **Silver :** données nettoyées et normalisées au format Parquet.
- **Gold :** tables analytiques prêtes pour le Data Warehouse.
- **Transformations :** PySpark.
- **Chargement final :** PostgreSQL, schéma `analytics`.
- **Vues ML :** PostgreSQL, schéma `ml`.
- **Planification :** Airflow, fréquence configurable via `JOBMARKET_AIRFLOW_SCHEDULE`.

### Exposition et visualisation

- API REST FastAPI avec documentation Swagger.
- Dashboard Streamlit pour les indicateurs, la recherche d'offres, l'analyse salaire optionnelle, le monitoring et les alertes mail.
- Monitoring Prometheus et Grafana.
- Masquage des colonnes techniques comme `job_id` dans l'interface.
- Vue cible Azure : Airflow, Azure Data Lake Gen2, traitements PySpark, PostgreSQL managé ou équivalent.

## 4. Calendrier de développement

| Phase | Durée estimée | Période |
| --- | ---: | --- |
| Rédaction du cahier des charges | 2 mois | Déc 2024 |
| Conception technique et fonctionnelle | 2 mois | Févr 2025 |
| Collecte et traitement de données | 6 mois | Août 2025 |
| Développement de l'application | 8 mois | Avril 2026 |
| Tests et validation | 2 mois | Juin 2026 |
| Déploiement et maintenance | 2 mois | Août 2026 |
| Soutenance | — | Sept 2026 |

## 5. Budget prévisionnel

Le projet est construit en priorité avec des composants open-source afin de rester réaliste pour un contexte étudiant. Le coût local est quasi nul hors temps humain. Une projection Azure est conservée pour montrer la trajectoire de déploiement professionnel.

| Ressource | Coût estimé |
| --- | ---: |
| Outils open-source : Python, PySpark, PostgreSQL, FastAPI, Streamlit | 0 € |
| API Adzuna en accès développeur | 0 € en phase projet |
| Connecteur The Muse et scraping encadré | 0 € hors maintenance |
| Exécution locale et base PostgreSQL locale | 0 € |
| Hébergement Azure cible pour MVP | Environ 80 à 350 €/mois selon volumétrie |
| Temps humain projet étudiant | Non facturé dans le budget technique |

## 6. Livrables

- Code source versionné dans le dossier Projet Fil Rouge.
- Pipeline de collecte et transformation PySpark.
- Base PostgreSQL `jobmarket` avec tables analytiques.
- API FastAPI avec endpoints de consultation.
- Dashboard Streamlit avec vues marché, compétences, entreprises et recommandations.
- Moteur de recherche interactif.
- Vues salaire optionnelles pour préparer une éventuelle prédiction.
- Monitoring Prometheus et Grafana.
- Alertes mail avec prévisualisation et SMTP optionnel.
- Documentation Markdown par bloc de compétences.
- Cahier des charges adapté au projet.
- Présentation PowerPoint de soutenance.

## 7. Utilisateurs finaux

### Persona 1 : Camille Martin, 24 ans - Candidate junior Data Analyst

Camille termine une formation en data analyse et cherche son premier poste en France. Elle consulte beaucoup d'offres, mais elle a du mal à savoir quelles compétences reviennent réellement et quelles villes offrent le plus d'opportunités.

**Objectif :** identifier les compétences prioritaires, les villes les plus actives et les offres accessibles à un profil junior.

**Comportement attendu :**

- Rechercher des offres par métier, ville et compétences.
- Comparer les technologies demandées comme SQL, Power BI, Python, cloud ou Databricks.
- Utiliser les recommandations pour cibler les candidatures les plus pertinentes.
- Observer les salaires disponibles pour mieux préparer ses entretiens.

### Persona 2 : Julien Moreau, 38 ans - Responsable formation data

Julien pilote une formation Data Engineer et veut aligner le contenu pédagogique avec les besoins du marché français. Il cherche des preuves concrètes pour prioriser les modules techniques à renforcer.

**Objectif :** suivre les compétences les plus demandées et adapter le programme de formation aux attentes des recruteurs.

**Comportement attendu :**

- Analyser les compétences les plus fréquentes dans les offres data.
- Identifier les technologies émergentes ou très demandées.
- Exploiter les graphiques pour justifier les choix pédagogiques.
- Exporter ou partager les indicateurs clés avec l'équipe pédagogique.

### Persona 3 : Sophie Lefèvre, 35 ans - Recruteuse tech / Lead Data

Sophie recrute des profils data pour une entreprise tech. Elle veut comprendre la concurrence sur le marché, les villes les plus actives et les compétences qui apparaissent dans les offres similaires.

**Objectif :** obtenir une vision synthétique du marché pour ajuster les intitulés de poste, les critères techniques et la stratégie de recrutement.

**Comportement attendu :**

- Suivre les indicateurs globaux du marché.
- Comparer les entreprises présentes dans le corpus.
- Consulter les offres concurrentes par ville et technologie.
- Utiliser l'API pour connecter les données à un outil interne si nécessaire.
- Déclencher une alerte mail pour surveiller certains mots-clés ou localisations.

## 8. Veille technologique

Les plateformes d'emploi évoluent vers des expériences plus ciblées, où la qualité des données, la fraîcheur des offres et la pertinence des recommandations deviennent différenciantes.

Pour les métiers data, l'enjeu est encore plus marqué car les intitulés varient fortement et les compétences techniques sont souvent noyées dans de longues descriptions.

### Innovations utiles au projet

- **Architecture Data Lakehouse :** séparation Bronze, Silver et Gold pour isoler les données brutes, nettoyées et analytiques.
- **Traitement distribué avec PySpark :** préparation à des volumes plus importants et à une montée en charge cloud.
- **Enrichissement par scraping contrôlé :** correction de la limite des descriptions tronquées afin d'améliorer l'extraction des technologies.
- **API et dashboard :** exposition rapide des résultats avec FastAPI et Streamlit.

### Solutions existantes

Les solutions comme LinkedIn, Indeed, HelloWork, Welcome to the Jungle, APEC ou Google for Jobs permettent déjà de rechercher des offres.

JobMarket ne cherche pas à les remplacer : le projet se positionne comme une couche analytique spécialisée data, capable de consolider, nettoyer et expliquer le marché à partir de sources externes.

## 9. Analyse SWOT

| Axe | Analyse |
| --- | --- |
| Forces | Pipeline réel, PySpark, modèle analytique PostgreSQL, API et dashboard déjà fonctionnels. |
| Faiblesses | Dépendance aux limites des APIs et besoin d'enrichissement HTML pour récupérer les descriptions complètes. |
| Opportunités | Forte demande de visibilité sur les métiers data, les compétences cloud/data et les tendances par ville. |
| Menaces | Évolution des conditions d'accès aux sites, limites de quotas, changement de structure HTML des pages sources. |

## 10. Critères d'acceptation du MVP

Le MVP est considéré comme acceptable si les critères suivants sont vérifiés :

1. La base contient uniquement de vraies offres et aucune source `sample`.
2. Aucune URL `example.com` n'est présente dans les données finales.
3. Le pipeline charge les données Bronze, Silver, Gold et PostgreSQL.
4. Les transformations principales utilisent PySpark.
5. Les descriptions Adzuna peuvent être enrichies depuis les liens stockés.
6. L'API répond sur les endpoints principaux.
7. Le dashboard affiche des villes françaises lisibles et masque les identifiants techniques.
8. Les compétences sont extraites et visibles dans les indicateurs.
9. Les recommandations sont explicables.
10. Les vues salaire optionnelles sont disponibles.
11. Le monitoring Prometheus/Grafana est opérationnel.
12. Les alertes mail fonctionnent en prévisualisation.
13. Les tests automatisés et le rapport qualité sont au vert.

## 11. État validé du MVP

- 2 028 offres réelles Adzuna France/data chargées dans PostgreSQL.
- 793 entreprises identifiées.
- 266 localisations normalisées.
- 773 lignes de compétences après enrichissement des descriptions.
- 10 recommandations générées.
- 2 028 lignes de features salaire, dont 380 exploitables pour entraînement.
- 49 descriptions Adzuna enrichies depuis les liens stockés en base.
- Monitoring Prometheus/Grafana opérationnel.
- 35 tests automatisés validés.

## 12. Sources et références

Les sources principales du projet sont :

- API Adzuna pour la collecte principale des offres d'emploi.
- API The Muse comme connecteur complémentaire prévu dans l'architecture.
- Documentation officielle Apache Spark et PySpark pour les transformations.
- Documentation Apache Airflow pour l'orchestration.
- Documentation PostgreSQL pour le stockage analytique.
- Documentation FastAPI et Streamlit pour l'exposition et la visualisation.
- Documentation Prometheus et Grafana pour le monitoring.
- Documentation Microsoft Azure pour la trajectoire cloud cible.

Ces références ont servi à cadrer les choix techniques, à sécuriser le pipeline et à rendre le projet rejouable dans un contexte local ou cloud.

## 13. Remerciements

Je remercie l'équipe pédagogique Liora ex DataScientest pour le cadre de projet, les retours méthodologiques et l'accompagnement technique. Ce projet m'a permis de relier les notions de Data Engineering vues en formation à un cas concret : collecter des données réelles, les fiabiliser, les transformer et les rendre utiles pour des utilisateurs métiers.

## Conclusion

Ce cahier des charges définit une version MVP réaliste, démontrable et soutenable de JobMarket Data Platform.

La solution répond à l'objectif principal : transformer des offres d'emploi data réelles en indicateurs exploitables, tout en préparant une trajectoire professionnelle vers Azure, l'orchestration Airflow et une industrialisation progressive.
