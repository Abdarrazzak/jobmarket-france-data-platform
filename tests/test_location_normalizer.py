from jobmarket.extract.location_normalizer import normalize_adzuna_location


def test_normalize_adzuna_location_uses_parent_city_for_arrondissement() -> None:
    location = normalize_adzuna_location(["France", "Ile-de-France", "Paris", "8eme arrondissement"])

    assert location["location_city"] == "Paris"
    assert location["location_region"] == "Ile-de-France"
    assert location["location_country"] == "France"


def test_normalize_adzuna_location_keeps_real_city() -> None:
    location = normalize_adzuna_location(["France", "Auvergne-Rhone-Alpes", "Lyon"])

    assert location["location_city"] == "Lyon"
