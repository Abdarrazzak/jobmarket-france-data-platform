FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml .
COPY src ./src
RUN pip install --no-cache-dir ".[dashboard]"

COPY dashboard ./dashboard

CMD ["streamlit", "run", "dashboard/app.py", "--server.address=0.0.0.0", "--server.port=8501"]
