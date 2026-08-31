# Hadoop Windows

## Objectif

Sous Windows, PySpark utilise des composants Hadoop pour lire et ecrire des fichiers locaux. Sans correctif Windows, Spark peut afficher des erreurs `winutils.exe`, `HADOOP_HOME` ou `hadoop.home.dir`.

## Installation realisee

Le projet utilise une installation minimale :

```text
C:\hadoop
C:\hadoop\bin\winutils.exe
C:\hadoop\bin\hadoop.dll
```

Variable d'environnement :

```text
HADOOP_HOME=C:\hadoop
```

## Pourquoi on ne met pas Hadoop dans le projet

Hadoop est une dependance systeme locale, comme PostgreSQL ou Java. Le code et les donnees du projet restent dans :

```text
C:\Users\abdho\Documents\Projet Fil Rouge
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

