# API

## Objectif

L'API FastAPI expose les donnees du Data Warehouse a des applications externes, notamment le dashboard Streamlit.

## Endpoints developpes

```text
GET /health
GET /jobs
GET /jobs/search
GET /search/options
GET /sources
GET /companies
GET /skills
GET /recommendations
GET /statistics
GET /ml/salary/features
GET /ml/salary/training
GET /ml/salary/metadata
GET /monitoring/warehouse
GET /metrics
POST /alerts/email/preview
POST /alerts/email/send
```

## Documentation Swagger

FastAPI genere automatiquement une documentation Swagger.

En local, elle sera disponible a cette adresse :

```text
http://localhost:8000/docs
```

## Principe de conception

L'API ne transforme pas les donnees lourdes. Elle lit des tables deja preparees dans PostgreSQL.

L'API expose des champs metier pour le dashboard. Les identifiants techniques restent dans PostgreSQL, mais ne sont pas affiches dans les endpoints principaux afin de fournir une restitution claire aux applications clientes.

Si PostgreSQL n'est pas disponible, l'API retourne des listes vides plutot que des donnees d'exemple. La base finale ne contient donc pas de fausses offres.

## Recherche et alertes

`GET /jobs/search` permet une recherche multicritere par mot-cle, ville, competences, contrat, experience, source et salaire minimum.

`POST /alerts/email/preview` reutilise le moteur de recherche pour generer une previsualisation d'alerte mail.

`POST /alerts/email/send` envoie le mail uniquement si les variables SMTP sont configurees. Sinon, l'API retourne un message clair et conserve le mode demonstration.

Pour Gmail, les variables SMTP sont a renseigner dans `.env` uniquement :

```text
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=<adresse_gmail_complete>
SMTP_PASSWORD=<mot_de_passe_application_google>
SMTP_FROM_EMAIL=<adresse_gmail_complete>
SMTP_USE_TLS=true
```

Le mot de passe attendu est un mot de passe d'application Google, pas le mot de passe principal du compte.

## Vues salaire optionnelles

Les endpoints `/ml/salary/*` exposent les vues PostgreSQL du schema `ml`. Elles sont utiles pour preparer une evolution analytique ou predictive, mais ne constituent pas une obligation IA du projet :

- features disponibles pour chaque offre ;
- dataset d'entrainement limite aux salaires exploitables ;
- metadonnees de qualite : lignes exploitables, lignes manquantes, bornes minimum et maximum.

## Monitoring

`GET /monitoring/warehouse` retourne l'etat du warehouse, la volumetrie, les controles qualite et l'audit d'enrichissement Adzuna.

`GET /metrics` expose les memes informations au format Prometheus pour Grafana.

Metriques Prometheus utiles pour la demonstration :

| Requete Prometheus | Interpretation attendue |
| --- | --- |
| `jobmarket_api_up` | API FastAPI disponible, `1` si OK |
| `jobmarket_postgres_up` | PostgreSQL disponible, `1` si OK |
| `jobmarket_jobs_total` | Nombre d'offres chargees dans le warehouse |
| `jobmarket_companies_total` | Nombre d'entreprises distinctes |
| `jobmarket_skills_total` | Nombre de lignes de competences detectees |
| `jobmarket_quality_status` | Qualite globale, `1` si PASS |
| `jobmarket_quality_blocking_issues_total` | Nombre d'anomalies qualite bloquantes |
| `jobmarket_description_enrichment_total` | Audit de l'enrichissement HTML Adzuna par statut |

Les metriques detaillees `jobmarket_fact_jobs_total`, `jobmarket_dim_company_total` et `jobmarket_fact_skills_total` restent exposees pour faire le lien avec le modele de donnees PostgreSQL.
