# API

## Objectif

L'API FastAPI expose les donnees du Data Warehouse a des applications externes, notamment le dashboard Streamlit.

## Endpoints minimaux

```text
GET /health
GET /jobs
GET /companies
GET /skills
GET /recommendations
GET /statistics
```

## Documentation Swagger

FastAPI genere automatiquement une documentation Swagger.

En local, elle sera disponible a cette adresse :

```text
http://localhost:8000/docs
```

## Principe de conception

L'API ne transforme pas les donnees lourdes. Elle lit des tables deja preparees dans PostgreSQL.

L'API expose des champs metier pour le dashboard. Les identifiants techniques restent dans PostgreSQL, mais ne sont pas affiches dans les endpoints principaux afin de garder une restitution lisible pour la soutenance.

Si PostgreSQL n'est pas disponible, l'API retourne des listes vides plutot que des donnees d'exemple. La base finale ne contient donc pas de fausses offres.
