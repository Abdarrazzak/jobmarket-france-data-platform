# 04 - BC04 Pilotage et accompagnement

## Objectif du pilotage

Le pilotage vise a livrer une plateforme Data Engineering demonstrable, maintenable et comprehensible par un jury technique.

## Methode projet

Approche iterative :

1. Cadrage du besoin.
2. Mise en place du socle projet.
3. Ingestion API.
4. Transformation PySpark.
5. Chargement PostgreSQL.
6. API et dashboard.
7. Qualite et documentation.
8. Preparation soutenance.

## Planning synthetique

| Phase | Objectif | Livrable |
| --- | --- | --- |
| Cadrage | Definir le besoin et le perimetre | Cahier des charges |
| Socle technique | Creer structure, Git, dependances | Depot executable |
| Ingestion | Collecter offres Adzuna | Bronze JSON |
| Transformation | Nettoyer avec PySpark | Silver et Gold Parquet |
| Serving | Charger PostgreSQL | Schemas analytics et serving |
| Restitution | API et dashboard | Swagger + Streamlit |
| Monitoring | Surveiller disponibilite et qualite | Prometheus + Grafana |
| Qualite | Tester et controler | Rapport PASS |
| Soutenance | Formaliser les preuves | PPT + Markdown |

## Suivi des risques

| Risque | Niveau | Action |
| --- | --- | --- |
| Quota API | Moyen | Limiter les pages, temporiser les appels |
| Description API tronquee | Fort | Enrichissement HTML Adzuna |
| Scraping instable | Moyen | Module optionnel, non bloquant |
| Configuration Windows Spark | Moyen | Hadoop minimal et fallback local |
| Manque de temps | Fort | Priorisation demo locale fonctionnelle |

## Qualite projet

Elements mis en place :

- tests automatises ;
- rapport qualite data ;
- separation du code par domaine ;
- documentation architecture et deploiement ;
- `.env` ignore par Git ;
- dashboard sans identifiants techniques visibles ;
- page Monitoring dans Streamlit ;
- metriques Prometheus et dashboards Grafana ;
- automatisation quotidienne ou hebdomadaire avec Airflow ;
- alertes mail en mode preview et SMTP optionnel ;
- suppression des donnees d'exemple dans la base finale.

## Accompagnement utilisateur

Pour faciliter la reprise :

- commandes documentees ;
- endpoints API simples ;
- dashboard Streamlit navigable ;
- scripts d'execution par etape ;
- docs de soutenance synthetiques ;
- choix techniques expliques dans les livrables.

## Decisions importantes

### Garder PySpark

PySpark est conserve comme moteur principal de transformation pour prouver la competence Data Engineering et permettre une montee en volume.

### Garder PostgreSQL

PostgreSQL sert de Data Warehouse de demonstration. Il structure les tables analytiques et alimente l'API.

### Desactiver le scraping non France

Le module de scraping existe, mais il est desactive dans la demo finale car la source testee ne correspond pas au perimetre France/data.

### Ne pas charger de fausses donnees

Les anciennes sources `*_sample` ont ete supprimees du pipeline final. La base ne contient plus d'URLs `example.com`.

## Indicateurs de pilotage

- 2 028 offres reelles chargees.
- 793 entreprises distinctes.
- 266 localisations normalisees.
- 773 lignes de competences detectees.
- 0 doublon detecte.
- 0 source sample.
- 0 URL example.com.
- 35 tests automatises valides.
- Dashboard et API disponibles localement.

## Conclusion BC04

Le pilotage a privilegie une demo robuste et explicable. Les arbitrages sont documentes, les risques principaux sont traites, et les utilisateurs peuvent reprendre le projet avec des commandes claires.
