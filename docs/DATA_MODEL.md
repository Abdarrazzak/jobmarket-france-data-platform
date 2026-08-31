# Modele de donnees

## Schemas PostgreSQL

Le Data Warehouse contient au minimum deux schemas :

- `analytics` pour les tables analytiques ;
- `serving` pour les vues ou tables optimisees pour l'API et le dashboard.

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
