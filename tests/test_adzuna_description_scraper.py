from jobmarket.enrich.adzuna_descriptions import AdzunaDescriptionScraper


def test_extract_description_from_jobposting_json_ld() -> None:
    html = """
    <html>
      <head>
        <script type="application/ld+json">
          {
            "@type": "JobPosting",
            "description": "<p>Build data pipelines with Python, SQL, PySpark, Airflow and Azure.</p>"
          }
        </script>
      </head>
      <body></body>
    </html>
    """

    description = AdzunaDescriptionScraper().extract_description(html)

    assert description == "Build data pipelines with Python, SQL, PySpark, Airflow and Azure."


def test_extract_description_from_html_block() -> None:
    html = """
    <main>
      <section class="job-description">
        Nous cherchons un Data Engineer pour construire des pipelines PySpark,
        orchestrer les traitements avec Airflow, modeliser en SQL et deployer sur Azure.
      </section>
    </main>
    """

    description = AdzunaDescriptionScraper().extract_description(html)

    assert description is not None
    assert "Data Engineer" in description
    assert "PySpark" in description
