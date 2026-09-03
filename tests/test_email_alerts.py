import pytest
from fastapi import HTTPException

from api.main import EmailAlertRequest, _build_alert_email, _smtp_configured, _validate_email_address


def test_build_alert_email_includes_filters_and_jobs() -> None:
    request = EmailAlertRequest(
        recipient_email="student@example.com",
        recipient_name="Abdho",
        query="data engineer",
        city="Paris",
        skills="Python,Azure",
        contract_type="CDI",
        limit=2,
    )
    jobs = [
        {
            "title": "Data Engineer Azure",
            "company_name": "DataCorp",
            "city": "Paris",
            "contract_type": "CDI",
            "salary_avg": 55000,
            "matched_skills": ["Azure", "Python"],
            "search_score": 29,
            "source_url": "https://example.org/job",
        }
    ]

    subject, body = _build_alert_email(request, jobs)

    assert subject == "Alerte JobMarket - 1 offres data - Paris"
    assert "Bonjour Abdho," in body
    assert "- Competences: Python,Azure" in body
    assert "Data Engineer Azure - DataCorp - Paris - CDI - 55 000 EUR - score 29" in body


def test_email_alert_default_limit_is_15() -> None:
    request = EmailAlertRequest(recipient_email="student@example.com")

    assert request.limit == 15


def test_smtp_configured_requires_host_and_sender() -> None:
    assert _smtp_configured({"host": "smtp.example.com", "from_email": "jobs@example.com"})
    assert not _smtp_configured({"host": "", "from_email": "jobs@example.com"})
    assert not _smtp_configured({"host": "smtp.example.com", "from_email": ""})


def test_gmail_smtp_requires_app_credentials() -> None:
    assert _smtp_configured(
        {
            "host": "smtp.gmail.com",
            "from_email": "jobmarket@gmail.com",
            "username": "jobmarket@gmail.com",
            "password": "app-password",
        }
    )
    assert not _smtp_configured({"host": "smtp.gmail.com", "from_email": "jobmarket@gmail.com"})


def test_validate_email_address_rejects_invalid_value() -> None:
    with pytest.raises(HTTPException):
        _validate_email_address("not-an-email")
