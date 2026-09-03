# 00 - README de transmission

## Projet

**JobMarket Data Platform** est une plateforme Data Engineering specialisee sur les offres data en France.

Le projet collecte de vraies offres d'emploi, les historise dans une logique Data Lake, les transforme avec PySpark, les charge dans PostgreSQL, puis les expose via FastAPI et Streamlit.

## Livrables fournis

- `00-readme-transmission.md` : guide de lecture et de reprise du projet.
- `01-bc01-conception-projet.md` : cadrage, objectifs, besoins et perimetre.
- `02-bc02-architecture-etl-analytique.md` : architecture Data, ETL, PySpark, API, recommandations et vues salaire optionnelles.
- `03-bc03-deploiement-solution.md` : installation, execution locale, Docker, cible Azure.
- `04-bc04-pilotage-accompagnement.md` : pilotage projet, qualite, risques, accompagnement.
- `05-bc04-analyse-financiere.md` : estimation financiere et arbitrages couts.
- `06-cahier-des-charges.md` : cahier des charges fonctionnel et technique.
- `06-cahier-des-charges.docx` : version Word adaptee a partir de l'exemple fourni.
- `07-rapport-final-consolide.md` : rapport final consolide couvrant conclusion, Git, secrets, deploiement, monitoring, bilan, suite, bibliographie et annexes.

## Etat valide apres chargement high volume

- Offres chargees : **2 028 vraies offres Adzuna France/data**.
- Entreprises : **793**.
- Localisations : **266**.
- Lignes de competences : **773** apres enrichissement HTML Adzuna.
- Recommandations : **10**.
- Vues salaire optionnelles : **2 028** lignes de features, dont **380** lignes exploitables pour entrainement.
- Rapport qualite : **PASS**.
- Donnees de demonstration supprimees : **0 source sample, 0 URL example.com**.

## Lancement rapide

Si l'environnement virtuel n'est pas encore installe :

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -e ".[all,dev,windows]"
```

```powershell
cd "<dossier_du_projet>"
.\.venv\Scripts\Activate.ps1
python scripts/run_local_pipeline.py --step all
```

Lancer l'API :

```powershell
python -m uvicorn api.main:app --host 127.0.0.1 --port 8000
```

Lancer le dashboard :

```powershell
python -m streamlit run dashboard\app.py --server.address 127.0.0.1 --server.port 8501 --server.headless true --browser.gatherUsageStats false
```

## URLs de demonstration

- API Swagger : http://127.0.0.1:8000/docs
- Dashboard Streamlit : http://127.0.0.1:8501
- Prometheus : http://localhost:9090
- Grafana : http://localhost:3000
- PostgreSQL : `localhost:5432`, base `jobmarket`

## Points d'attention

Les secrets API sont dans `.env`, fichier ignore par Git. Ils ne doivent pas etre commits.

Le scraping web est optionnel. Le dataset final de demonstration conserve uniquement les vraies offres Adzuna France pour rester coherent avec le sujet "offres data en France".

L'API Adzuna limite la description retournee. Une etape `backfill_adzuna_descriptions` lit les URLs stockees dans PostgreSQL, scrape les pages de detail, remplace les descriptions tronquees quand une meilleure version existe, puis recalcule les competences et les recommandations.

## Verification

```powershell
python -m pytest
```

Resultat attendu : **35 tests passed**.
