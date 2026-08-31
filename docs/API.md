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

Si PostgreSQL n'est pas encore disponible pendant une demonstration locale, l'API retourne des donnees d'exemple. Cela permet de demontrer Swagger et Streamlit meme avant le chargement complet.
