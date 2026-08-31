# JobMarket Data Platform

## Objectif

JobMarket Data Platform est un projet Data Engineering qui analyse le marche de l'emploi a partir de plusieurs sources d'offres.

Le projet doit demontrer :

- une ingestion multi-sources ;
- un Data Lake Azure en couches Bronze, Silver et Gold ;
- des transformations PySpark ;
- une orchestration avec Apache Airflow ;
- un Data Warehouse PostgreSQL ;
- une API FastAPI ;
- un dashboard Streamlit ;
- un moteur de recommandation simple et explicable ;
- une execution conteneurisee avec Docker ;
- une documentation professionnelle.

## Architecture cible

```text
Adzuna API + The Muse API
        |
        v
Apache Airflow
        |
        v
Azure Data Lake Storage Gen2
        |
        +--> Bronze: JSON brut historise
        |
        +--> Silver: Parquet nettoye et harmonise
        |
        +--> Gold: Parquet enrichi pour analytics
        |
        v
PostgreSQL Data Warehouse
        |
        +--> FastAPI
        |
        +--> Streamlit
```

## Structure du depot

```text
dags/                  DAG Airflow
src/jobmarket/         Code Python du pipeline
api/                   Application FastAPI
dashboard/             Application Streamlit
configs/               Fichiers de configuration
docs/                  Documentation projet
tests/                 Tests automatises
scripts/               Scripts utiles
data/local/            Donnees locales temporaires ignorees par Git
```

## Demarrage local

1. Creer un environnement Python.
2. Installer les dependances.
3. Copier `.env.example` vers `.env`.
4. Renseigner les identifiants API et Azure.
5. Lancer les tests.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
copy .env.example .env
pytest
```

## Documentation

- [Architecture](docs/ARCHITECTURE.md)
- [Modele de donnees](docs/DATA_MODEL.md)
- [API](docs/API.md)
- [PostgreSQL](docs/POSTGRESQL.md)
- [Deploiement](docs/DEPLOYMENT.md)
- [Roadmap](docs/ROADMAP.md)
- [Script de demonstration](docs/DEMO.md)
- [Fiche de soutenance](docs/SOUTENANCE.md)

## Demo rapide

Sans Docker :

```powershell
.\.venv\Scripts\Activate.ps1
$env:PYTHONPATH="C:\Users\abdho\Documents\Projet Fil Rouge\src"
python scripts/run_local_pipeline.py --step all --skip-postgres
uvicorn api.main:app --reload
streamlit run dashboard/app.py
```

Avec Docker :

```powershell
docker compose up -d --build
```
