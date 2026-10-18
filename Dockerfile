# Backend image. Models/reports/data are mounted at runtime (see docker-compose.yml); train first on the host.
FROM python:3.12-slim
WORKDIR /srv
COPY backend/requirements.txt backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt gunicorn
COPY backend backend
COPY ml ml
ENV PYTHONPATH=/srv:/srv/backend MODELS_DIR=/srv/models REPORTS_DIR=/srv/reports DATA_PATH=/srv/data/raw/creditcard.csv
EXPOSE 5000
CMD ["gunicorn", "-b", "0.0.0.0:5000", "-w", "2", "--timeout", "60", "app:create_app()"]
