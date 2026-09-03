# Modele de donnees

## Schemas PostgreSQL

Le Data Warehouse contient au minimum deux schemas :

- `analytics` pour les tables analytiques ;
- `serving` pour les vues ou tables optimisees pour l'API et le dashboard ;
- `ml` pour les vues salaire optionnelles.

## Tables minimales

### analytics.fact_jobs

Table centrale des offres d'emploi.

Colonnes attendues :

- `job_id`
- `source`
- `title`
- `company_id`
- `location_id`
- `contract_type`
- `experience_level`
- `salary_min`
- `salary_max`
- `salary_avg`
- `description`
- `publication_date`
- `load_date`
- `ingestion_timestamp`

### analytics.dim_company

Referentiel des entreprises.

Colonnes attendues :

- `company_id`
- `company_name`
- `source`
- `load_date`
- `ingestion_timestamp`

### analytics.dim_location

Referentiel des localisations.

Colonnes attendues :

- `location_id`
- `city`
- `region`
- `country`
- `source`
- `load_date`
- `ingestion_timestamp`

### analytics.fact_skills

Table des competences detectees dans les offres.

Colonnes attendues :

- `job_id`
- `skill_name`
- `source`
- `load_date`
- `ingestion_timestamp`

### analytics.job_recommendations

Table des recommandations explicables.

Colonnes attendues :

- `recommendation_id`
- `job_id`
- `input_skills`
- `score`
- `score_details`
- `load_date`
- `ingestion_timestamp`

### analytics.description_enrichment_log

Table d'audit de l'enrichissement HTML Adzuna.

Colonnes attendues :

- `job_id`
- `source_url`
- `status`
- `original_length`
- `enriched_length`
- `error_message`
- `scraped_at`

## Vues serving

### serving.jobs_public

Vue lisible des offres pour FastAPI et Streamlit. Elle masque les details techniques inutiles a l'utilisateur et joint les entreprises et localisations.

### serving.market_by_city

Vue d'analyse de la volumetrie d'offres par ville, triee pour l'affichage du marche de l'emploi.

### serving.skill_demand

Vue de demande par competence detectee.

## Vues salaire optionnelles

### ml.salary_prediction_features

Vue de features pour analyser les salaires disponibles et preparer une eventuelle prediction a partir des champs disponibles :

- titre ;
- entreprise ;
- ville ;
- region ;
- contrat ;
- experience ;
- source ;
- competences ;
- salaire cible quand disponible ;
- indicateur de qualite du salaire.

### ml.salary_training_dataset

Sous-ensemble exploitable pour entrainement, avec salaires presents et bornes metier coherentes.

### ml.salary_inference_dataset

Sous-ensemble contenant les offres sans salaire exploitable ou a predire.

### ml.salary_prediction_metadata

Vue de synthese pour piloter la qualite du dataset salaire : nombre de lignes, salaires minimum et maximum retenus, lignes exclues.
