# 05 - Analyse financiere

## Objectif

Cette analyse estime les couts d'une industrialisation cloud du projet JobMarket Data Platform sur Azure, en partant de la version locale de demonstration.

## Version actuelle

Le MVP fonctionne localement :

- stockage local `data/local` ;
- PostgreSQL local ;
- API et dashboard locaux ;
- orchestration Airflow en Docker possible ;
- aucune consommation Azure obligatoire pour la demo.

Cout local direct : **0 euro d'infrastructure cloud**, hors machine de developpement.

## Hypothese de deploiement Azure

Architecture cible :

- Azure Data Lake Storage Gen2 ;
- Azure Databricks ou Synapse Spark ;
- Azure Database for PostgreSQL ;
- Azure Container Apps ou App Service ;
- Azure Key Vault ;
- Azure Monitor.

## Estimation mensuelle indicative

| Poste | Usage cible | Estimation |
| --- | --- | --- |
| Data Lake Storage Gen2 | fichiers Bronze, Silver, Gold | 5 a 20 EUR |
| Spark managé | jobs batch ponctuels | 30 a 150 EUR |
| PostgreSQL managé | petite base analytique | 25 a 100 EUR |
| API FastAPI | container leger | 5 a 30 EUR |
| Dashboard Streamlit | container leger | 5 a 30 EUR |
| Logs et monitoring | supervision minimale | 5 a 20 EUR |
| Secrets Key Vault | quelques secrets | 1 a 5 EUR |

Estimation MVP cloud : **76 a 355 EUR / mois** selon frequence de traitement, taille des clusters et niveau de service.

## Leviers d'optimisation

- Lancer Spark uniquement en batch planifie.
- Garder des fichiers Parquet compresses.
- Limiter la retention Silver/Gold si necessaire.
- Utiliser une base PostgreSQL dimensionnee modestement au depart.
- Eviter un cluster Spark permanent.
- Mettre des alertes budget Azure.

## Valeur produite

La plateforme permet :

- d'identifier les competences data prioritaires ;
- de suivre les villes qui recrutent ;
- d'analyser les entreprises actives ;
- d'aider un candidat a cibler ses apprentissages ;
- de produire une veille marche reproductible.

## Cout d'opportunite

Sans pipeline automatise :

- collecte manuelle lente ;
- donnees non historisees ;
- analyses difficiles a reproduire ;
- absence de controle qualite ;
- decisions formation ou candidature moins fiables.

## Choix du deploiement local

Le deploiement local permet de valider la chaine technique sans engager de cout d'infrastructure Azure pendant la phase MVP.

L'architecture Azure est documentee pour montrer la trajectoire industrielle sans imposer un cout cloud pendant la phase projet.

## Conclusion financiere

Le projet est peu couteux en local et peut etre industrialise progressivement. Le principal cout cloud viendrait du calcul Spark, qui doit etre lance a la demande plutot que maintenu en continu.
