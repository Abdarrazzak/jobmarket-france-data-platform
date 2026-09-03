# Hadoop Windows

## Objectif

Sous Windows, PySpark utilise des composants Hadoop pour lire et ecrire des fichiers locaux. Sans correctif Windows, Spark peut afficher des erreurs `winutils.exe`, `HADOOP_HOME` ou `hadoop.home.dir`.

## Installation realisee

Le projet utilise une installation minimale :

```text
<chemin_hadoop_local>
<chemin_hadoop_local>\bin\winutils.exe
<chemin_hadoop_local>\bin\hadoop.dll
```

Variable d'environnement :

```text
HADOOP_HOME=<chemin_hadoop_local>
```

## Pourquoi on ne met pas Hadoop dans le projet

Hadoop est une dependance systeme locale, comme PostgreSQL ou Java. Le code et les donnees du projet restent dans :

```text
<dossier_du_projet>
```

## Test de validation

```powershell
$env:SPARK_FORCE_HADOOP_IO="1"
python scripts/run_local_pipeline.py --step all
```

Resultat attendu :

- Bronze vers Silver : OK
- Silver vers Gold : OK
- chargement PostgreSQL : OK
- rapport qualite : PASS
