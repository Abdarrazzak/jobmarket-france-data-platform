from __future__ import annotations

import re


def normalize_adzuna_location(area: list[str], display_name: str | None = None) -> dict[str, str | None]:
    cleaned_area = [_clean_part(part) for part in area if _clean_part(part)]
    country = cleaned_area[0] if cleaned_area else "France"
    region = cleaned_area[1] if len(cleaned_area) >= 2 else None
    city = _infer_city(cleaned_area, display_name)

    return {
        "location_city": city,
        "location_region": region,
        "location_country": country,
    }


def _infer_city(area: list[str], display_name: str | None = None) -> str | None:
    if len(area) >= 4 and _is_arrondissement(area[-1]):
        return area[-2]
    if len(area) >= 3:
        return area[-1]

    display_city = _city_from_display_name(display_name)
    if display_city and display_city.lower() != "france":
        return display_city

    return None


def _city_from_display_name(display_name: str | None) -> str | None:
    if not display_name:
        return None
    return _clean_part(display_name.split(",")[0])


def _is_arrondissement(value: str) -> bool:
    return bool(re.search(r"arrondissement", value, flags=re.IGNORECASE))


def _clean_part(value: str | None) -> str | None:
    if value is None:
        return None
    return re.sub(r"\s+", " ", value).strip() or None
