# 01 - BC01 Conception du projet

## Contexte

Les metiers data evoluent rapidement et les technologies demandees changent selon les entreprises, les villes et les niveaux d'experience. Le projet vise a construire une plateforme capable d'analyser les offres d'emploi data en France afin d'identifier les tendances du marche.

## Probleme a resoudre

Les offres d'emploi sont dispersees sur plusieurs sources. Les descriptions sont parfois incompletes, les donnees ne sont pas homogenes et les competences techniques ne sont pas structurees. Sans pipeline de donnees, il est difficile de repondre de maniere fiable aux questions suivantes :

- Quelles competences data sont les plus demandees ?
- Quelles entreprises recrutent ?
- Quelles villes concentrent les offres ?
- Quels salaires sont proposes lorsque l'information est disponible ?
- Quelles offres correspondent a un profil donne ?

## Objectifs du projet

- Collecter de vraies offres data en France.
- Historiser les donnees brutes.
- Nettoyer et harmoniser les sources.
- Construire des tables analytiques exploitables.
- Extraire automatiquement les competences techniques.
- Proposer des recommandations d'offres explicables.
- Mettre a disposition une recherche interactive et des vues salaire optionnelles.
- Exposer les resultats via API et dashboard.
- Superviser la plateforme avec Prometheus et Grafana.
- Documenter une trajectoire d'evolution possible vers Azure.

## Perimetre fonctionnel

Inclus :

- Ingestion Adzuna API.
- Connecteur The Muse API.
- Module web scraping optionnel.
- Data Lake logique Bronze, Silver, Gold.
- Transformations PySpark.
- Data Warehouse PostgreSQL.
- API FastAPI.
- Dashboard Streamlit.
- Recherche multicritere.
- Vues salaire optionnelles.
- Alertes mail optionnelles.
- Monitoring Prometheus et Grafana.
- Orchestration Airflow.
- Docker Compose.
- Tests automatises et documentation.

Exclu ou limite :

- LinkedIn non utilise.
- Web scraping non bloquant.
- Modele de recommandation volontairement simple et explicable.
- Azure Data Lake Gen2 presente comme piste d'evolution ; le MVP utilise le stockage local `data/local`.

## Utilisateurs cibles

- Candidat data : comprendre les competences a renforcer.
- Responsable formation : identifier les technologies a enseigner.
- Recruteur : visualiser les villes, entreprises et tendances.
- Jury : evaluer la maitrise du cycle Data Engineering complet.

## Indicateurs de succes

- Pipeline executable de bout en bout.
- Donnees reelles chargees dans PostgreSQL.
- Rapport qualite en statut PASS.
- Dashboard consultable localement.
- API documentee automatiquement par Swagger.
- Code versionne et livrables structurés.

## Resultats obtenus

- 2 028 offres Adzuna France chargees.
- 793 entreprises distinctes.
- 266 localisations.
- 773 lignes de competences apres enrichissement HTML.
- 10 recommandations generees.
- 2 028 lignes de features salaire, dont 380 exploitables pour entrainement et 1 648 a predire ou incompletes.
- 0 donnees d'exemple dans la base finale.

## Risques identifies

| Risque | Impact | Reponse |
| --- | --- | --- |
| Quotas API Adzuna | Collecte incomplete | Pagination controlee et delai entre appels |
| Descriptions tronquees | Extraction de skills moins precise | Backfill HTML depuis les URLs Adzuna |
| Localisations trop fines | Graphiques peu lisibles | Normalisation des villes en PySpark |
| Scraping instable | Echec pipeline | Scraping optionnel et desactive dans la demo finale |
| Docker non disponible | Demo bloquee | Scenario local sans Docker documente |

## Conclusion BC01

La conception couvre un besoin concret d'analyse du marche data en France. Le projet demontre une chaine Data Engineering complete, depuis la collecte jusqu'a la restitution, avec des choix techniques justifies et des limites explicites.
