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
- Streamlit pour le dashboard ;
- Prometheus pour la collecte de metriques ;
- Grafana pour les tableaux de bord de monitoring.

L'image Docker Airflow installe Java 17 afin d'executer les transformations PySpark dans le conteneur sans dependre du Java installe sur le poste Windows.

## Variables d'environnement

Les secrets ne doivent jamais etre commits dans Git.

Le fichier `.env.example` documente les variables attendues.

Le fichier `.env` reste local et est ignore par Git.

Avant publication du depot, un controle peut verifier que les valeurs locales de `.env` ne sont pas presentes dans les fichiers du projet :

```powershell
python scripts/check_no_secrets.py
```

Variables principales :

- identifiants Adzuna ;
- chemins locaux Bronze, Silver, Gold ;
- connexion PostgreSQL ;
- ports API et dashboard ;
- frequence Airflow via `JOBMARKET_AIRFLOW_SCHEDULE` ;
- parametres de backfill HTML ;
- compte Grafana ;
- parametres SMTP optionnels pour les alertes mail.

## Configuration SMTP Gmail

Les vraies valeurs SMTP doivent etre placees uniquement dans `.env`, jamais dans le code, jamais dans Streamlit, jamais dans GitHub et jamais dans les logs.

Pour Gmail ou Google Workspace avec authentification SMTP classique :

```text
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=<adresse_gmail_complete>
SMTP_PASSWORD=<mot_de_passe_application_google>
SMTP_FROM_EMAIL=<adresse_gmail_complete>
SMTP_FROM_NAME=JobMarket Alerting
SMTP_USE_TLS=true
```

Bonnes pratiques :

- activer la validation en deux etapes sur le compte Google ;
- generer un mot de passe d'application Google dedie a JobMarket ;
- ne pas utiliser le mot de passe principal du compte Gmail ;
- ne jamais commiter `.env` ;
- relancer FastAPI apres modification de `.env` ;
- lancer `python scripts/check_no_secrets.py` avant chaque push GitHub.

En production, remplacer ce mode local par un coffre de secrets, par exemple Azure Key Vault, et par un compte technique dedie.

## Planification Airflow

Le DAG `jobmarket_pipeline` automatise la collecte et le traitement complet.

Par defaut :

```text
JOBMARKET_AIRFLOW_SCHEDULE=@daily
```

Exemple hebdomadaire, chaque lundi a 06:00 :

```text
JOBMARKET_AIRFLOW_SCHEDULE=0 6 * * 1
```

Le DAG utilise `catchup=False` pour eviter de rejouer automatiquement tous les jours manques, `max_active_runs=1` pour eviter les executions concurrentes, et un timeout de 3 heures par run.

## Ports locaux

- Airflow : http://localhost:8080
- FastAPI : http://localhost:8000/docs
- Streamlit : http://localhost:8501
- Prometheus : http://localhost:9090
- Grafana : http://localhost:3000
- PostgreSQL : localhost:5432

## Monitoring local separe

Si l'API est lancee hors Docker sur `127.0.0.1:8000`, le monitoring peut etre lance seul :

```powershell
docker compose -f docker-compose.monitoring.yml up -d prometheus grafana
```

Prometheus utilise alors `host.docker.internal:8000` pour interroger l'endpoint `/metrics` de l'API locale.

## Requetes Prometheus de controle

Dans `http://localhost:9090`, onglet **Query**, les requetes principales a tester sont :

```promql
jobmarket_api_up
jobmarket_postgres_up
jobmarket_jobs_total
jobmarket_quality_status
jobmarket_quality_blocking_issues_total
```

Resultats attendus pour une demo stable :

- `jobmarket_api_up = 1` ;
- `jobmarket_postgres_up = 1` ;
- `jobmarket_jobs_total = 2028` ;
- `jobmarket_quality_status = 1` ;
- `jobmarket_quality_blocking_issues_total = 0`.
