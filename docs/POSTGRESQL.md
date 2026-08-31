# PostgreSQL

## Objectif

PostgreSQL sert de Data Warehouse. Il ne remplace pas le Data Lake : les fichiers Bronze, Silver et Gold restent dans le stockage fichier, puis PostgreSQL expose les tables analytiques.

## Parametres locaux

```text
host: localhost
port: 5432
database: jobmarket
user: jobmarket
password: jobmarket
```

## Installation Windows

Installer PostgreSQL 16 ou 17 avec l'installateur EDB.

Pendant l'installation :

```text
Password postgres: jobmarket
Port: 5432
Locale: Default
Stack Builder: decoche
```

## Creation de la base

Ouvrir SQL Shell `psql`, se connecter avec l'utilisateur `postgres`, puis executer :

```sql
CREATE USER jobmarket WITH PASSWORD 'jobmarket';
CREATE DATABASE jobmarket OWNER jobmarket;
GRANT ALL PRIVILEGES ON DATABASE jobmarket TO jobmarket;
```

## Chargement des donnees Gold

Quand PostgreSQL est pret :

```powershell
cd "C:\Users\abdho\Documents\Projet Fil Rouge"
.\.venv\Scripts\Activate.ps1
$env:PYTHONPATH="C:\Users\abdho\Documents\Projet Fil Rouge\src"
python scripts/run_local_pipeline.py --step load_postgres
```

Cette commande cree les schemas `analytics` et `serving`, puis charge :

- `analytics.fact_jobs`
- `analytics.dim_company`
- `analytics.dim_location`
- `analytics.fact_skills`
- `analytics.job_recommendations`

## Verification SQL

```sql
SELECT COUNT(*) FROM analytics.fact_jobs;
SELECT COUNT(*) FROM analytics.dim_company;
SELECT skill_name, COUNT(*) FROM analytics.fact_skills GROUP BY skill_name ORDER BY COUNT(*) DESC;
SELECT title, company_name, score FROM analytics.job_recommendations ORDER BY score DESC;
```

