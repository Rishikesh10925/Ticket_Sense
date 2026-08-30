FROM python:3.12-slim
WORKDIR /app

COPY backend/pyproject.toml ./
COPY backend/app ./app
# .[ai]: the live evidence endpoint (app/services/retrieval.py) needs
# sentence-transformers at runtime now, not just for the one-off embedding scripts —
# same reasoning as scikit-learn moving to core deps in Week 4 for classification.
RUN pip install --no-cache-dir ".[ai]"

COPY ai /ai

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
