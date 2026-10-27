# Backend image. NOTE: written but not built/verified in the authoring environment (no Docker available).
FROM python:3.12-slim
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 FLASK_HOST=0.0.0.0
COPY backend/requirements.txt backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt
COPY ml ml
COPY backend backend
# data/, models/ and reports/ are mounted read-only by docker-compose; they are not baked into the image.
WORKDIR /app/backend
EXPOSE 5000
CMD ["python", "run.py"]
