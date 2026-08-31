# Deploiement

## Objectif

Le deploiement final doit permettre de lancer les composants principaux avec une seule commande.

```powershell
docker compose up -d
```

## Services cibles

- Airflow pour l'orchestration ;
- PostgreSQL pour le Data Warehouse ;
- FastAPI pour l'API REST ;
- Streamlit pour le dashboard.

## Variables d'environnement

Les secrets ne doivent jamais etre commits dans Git.

Le fichier `.env.example` documente les variables attendues.

Le fichier `.env` reste local et est ignore par Git.

## Ports locaux

- Airflow : http://localhost:8080
- FastAPI : http://localhost:8000/docs
- Streamlit : http://localhost:8501
- PostgreSQL : localhost:5432
