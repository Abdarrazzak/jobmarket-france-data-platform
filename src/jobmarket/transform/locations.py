from __future__ import annotations

from pyspark.sql import Column
from pyspark.sql import functions as F


ACCENTED_CHARS = "àâäáãåçéèêëíìîïôöóòõùûüúÿñîï"
ASCII_CHARS = "aaaaaaceeeeiiiiooooouuuuynii"

NON_CITY_TERMS = [
    "ain",
    "aisne",
    "allier",
    "alpes-maritimes",
    "ardeche",
    "ardennes",
    "ariege",
    "aube",
    "auvergne-rhone-alpes",
    "bas-rhin",
    "bouches-du-rhone",
    "bretagne",
    "centre",
    "charente",
    "cher",
    "correze",
    "cote-d-or",
    "doubs",
    "drome",
    "essonne",
    "france",
    "gard",
    "grand-est",
    "haute-garonne",
    "haute-savoie",
    "hauts-de-france",
    "hauts-de-seine",
    "herault",
    "ile-de-france",
    "ille-et-vilaine",
    "indre-et-loire",
    "isere",
    "loire",
    "loire-atlantique",
    "loiret",
    "maine-et-loire",
    "marne",
    "meurthe-et-moselle",
    "moselle",
    "nord",
    "nouvelle-aquitaine",
    "occitanie",
    "paris departement",
    "pas-de-calais",
    "pays de la loire",
    "provence-alpes-cote d azur",
    "remote",
    "rhone",
    "saone-et-loire",
    "seine-et-marne",
    "seine-maritime",
    "seine-saint-denis",
    "teletravail",
    "val-de-marne",
    "val-d-oise",
    "var",
    "vaucluse",
    "yvelines",
]

NON_CITY_PATTERN = f"^({'|'.join(NON_CITY_TERMS)})$"


def normalize_city(city: Column, region: Column) -> Column:
    cleaned_city = F.regexp_replace(F.trim(city), r"\s*,\s*France$", "")
    cleaned_region = F.trim(region)
    city_key = _normalize_key(cleaned_city)
    region_key = _normalize_key(cleaned_region)

    inferred_parent_city = (
        F.when(region_key.contains("paris"), F.lit("Paris"))
        .when(region_key.contains("lyon"), F.lit("Lyon"))
        .when(region_key.contains("marseille"), F.lit("Marseille"))
        .otherwise(F.lit(None))
    )

    return (
        F.when(cleaned_city.isNull() | (F.length(cleaned_city) == 0), F.lit(None))
        .when(city_key.rlike(NON_CITY_PATTERN), F.lit(None))
        .when(city_key.rlike("arrondissement"), F.coalesce(inferred_parent_city, F.lit("Paris")))
        .when(city_key.rlike(r"^paris(\s|-|,|$)"), F.lit("Paris"))
        .when(city_key.rlike(r"^lyon(\s|-|,|$)"), F.lit("Lyon"))
        .when(city_key.rlike(r"^marseille(\s|-|,|$)"), F.lit("Marseille"))
        .when(city_key.rlike(r"^lille(\s|-|,|$)"), F.lit("Lille"))
        .when(city_key.rlike(r"^aix en provence"), F.lit("Aix-en-Provence"))
        .otherwise(cleaned_city)
    )


def _normalize_key(column: Column) -> Column:
    normalized = F.lower(F.translate(column, ACCENTED_CHARS, ASCII_CHARS))
    normalized = F.regexp_replace(normalized, r"['’]", "-")
    normalized = F.regexp_replace(normalized, r"\s+", " ")
    return normalized
