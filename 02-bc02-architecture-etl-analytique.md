# 02 - BC02 Architecture ETL, Cloud et analytique avancee

## Vue d'ensemble

L'architecture suit une logique ELT moderne :

```text
Adzuna API + The Muse API + Web scraping optionnel
        |
        v
Airflow
        |
        v
Bronze JSON historise
        |
        v
Silver Parquet nettoye avec PySpark
        |
        v
Gold Parquet analytique avec PySpark
        |
        v
PostgreSQL
        |
        +--> FastAPI
        +--> Streamlit
        +--> Prometheus + Grafana
```

La partie IA n'est pas presentee comme une obligation du projet. Le coeur du livrable est Data Engineering : collecte, PySpark, modelisation, PostgreSQL, API, dashboard, orchestration et monitoring. Les vues salaire et les recommandations sont des options analytiques permettant de valoriser les donnees, sans remplacer les objectifs principaux.

## Architecture cible Azure

En cible cloud, les couches de donnees sont portees par Azure Data Lake Storage Gen2 :

- Container `bronze` : donnees brutes JSON, append-only.
- Container `silver` : donnees nettoyees et harmonisees, format Parquet.
- Container `gold` : donnees metier pretes pour l'analyse.

Les traitements PySpark peuvent etre executes localement pour la soutenance, puis portes vers Azure Databricks ou Synapse Spark dans une version industrialisee.

## Sources de donnees

### Adzuna API

Source principale du dataset final. Le plan de collecte cible :

- pays `fr` ;
- metiers data : Data Engineer, Data Analyst, Data Scientist, Analytics Engineer, BI Analyst, Machine Learning Engineer, Data Architect, Consultant Data ;
- recherche France entiere ;
- pagination controlee ;
- delai entre appels pour respecter les quotas.

### The Muse API

Connecteur disponible pour l'extension multi-source. Les resultats sont filtres sur le perimetre France/data avant chargement final.

### Web scraping optionnel

Le module de scraping est present pour demontrer l'integration d'une page HTML. Il est desactive dans la demo finale car la source testee retourne surtout des offres remote internationales, hors perimetre France.

## Couches de donnees

### Bronze

Objectif : conserver les donnees brutes recues.

Caracteristiques :

- format JSONL ;
- partition par source, date et run ;
- pas de modification destructive ;
- utile pour rejouer le pipeline.

### Silver

Objectif : nettoyer et harmoniser.

Traitements :

- schema commun entre sources ;
- identifiant `job_id` stable ;
- nettoyage titres, entreprises, localisations ;
- suppression des doublons ;
- typage des salaires et dates ;
- normalisation des villes avec PySpark.

### Gold

Objectif : servir l'analyse metier.

Tables produites :

- `fact_jobs` ;
- `dim_company` ;
- `dim_location` ;
- `fact_skills` ;
- `job_recommendations` ;
- `statistics` ;
- `skill_trends` ;
- vues `ml.salary_*` pour l'analyse salaire optionnelle.

## Usage de PySpark

PySpark est utilise pour les transformations principales :

- lecture Bronze JSON ;
- nettoyage vers Silver ;
- generation des dimensions et faits Gold ;
- extraction des competences par expressions regulieres Spark ;
- calcul des indicateurs et recommandations.

Ce choix montre une architecture adaptee a un volume croissant, meme si la demo locale reste volontairement limitee.

## Enrichissement HTML Adzuna

Limite constatee : l'API Adzuna tronque souvent les descriptions.

Solution :

1. Charger les offres dans PostgreSQL.
2. Lire les URLs Adzuna stockees dans `analytics.fact_jobs`.
3. Scraper la page HTML de detail.
4. Extraire une description plus longue via JSON-LD, meta description ou blocs HTML.
5. Mettre a jour la description si elle est meilleure.
6. Recalculer `fact_skills` et `job_recommendations`.

Resultat final verifie :

- 49 descriptions mises a jour lors du dernier backfill.
- 1 description ignoree car aucune version plus longue n'etait disponible.
- 773 lignes de competences extraites.

## Vues salaire optionnelles

Le schema PostgreSQL `ml` expose des vues qui peuvent servir a preparer une prediction de salaires, mais cette partie reste optionnelle dans le projet :

- `ml.salary_prediction_features` : features par offre ;
- `ml.salary_training_dataset` : lignes avec salaire exploitable ;
- `ml.salary_inference_dataset` : lignes sans salaire fiable ou a predire ;
- `ml.salary_prediction_metadata` : statistiques de controle.

Les features combinent titre, entreprise, localisation, contrat, experience, source et competences detectees. Elles servent surtout a montrer que le pipeline produit un dataset exploitable pour une evolution analytique.

## Moteur de recommandation

Le moteur de recommandation est explicable.

Score :

```text
score = competences_matchees * 10
      + bonus_localisation
      + bonus_contrat
      + bonus_experience
```

Profil de test :

- competences : Python, SQL, PySpark, Azure ;
- localisation : Paris ;
- niveau : junior ;
- contrat : CDI.

Meilleure recommandation observee :

```text
Data Engineer Databricks F/H - Datatorii - Paris - score 43
```

## Qualite des donnees

Controles automatises :

- unicite de `job_id` ;
- titres non vides ;
- entreprises non vides ;
- sources non vides ;
- detection de doublons ;
- schema attendu ;
- rapport qualite JSON.

Dernier rapport :

```text
status = PASS
total_rows = 2028
duplicate_job_ids = 0
```

## Monitoring

FastAPI expose `/monitoring/warehouse` pour le dashboard et `/metrics` pour Prometheus. Grafana affiche la disponibilite API/PostgreSQL, les volumes du warehouse, les controles qualite et les indicateurs salaire. Les requetes Prometheus de demonstration sont `jobmarket_api_up`, `jobmarket_postgres_up`, `jobmarket_jobs_total`, `jobmarket_quality_status` et `jobmarket_quality_blocking_issues_total`.

## Conclusion BC02

L'architecture separe clairement ingestion, stockage, transformation, serving et visualisation. PySpark porte les transformations data, PostgreSQL sert le Data Warehouse, FastAPI et Streamlit assurent la restitution, et l'enrichissement HTML corrige une limite reelle de l'API Adzuna.
