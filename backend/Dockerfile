FROM python:3.12-slim
WORKDIR /app

# The repo's directory layout is preserved as-is (backend/, ai/, db/) rather than
# flattened, because several modules compute sibling-directory paths relative to
# their own file location at runtime — app/routers/analytics.py's `parents[3] / "ai"`
# and db/migrations/env.py's `parents[2] / "backend"` both assume this same shape
# locally (see those files' own comments), so the image mirrors it instead of
# special-casing container paths.
# Dependencies first, application code last: a code change then reuses the cached
# torch / sentence-transformers layers instead of reinstalling them (minutes vs seconds).
COPY backend/pyproject.toml ./backend/
# CPU-only torch/torchvision, installed *before* the [ai] extra below — easyocr and
# sentence-transformers both depend on torch, and left to its own resolution pip
# pulls the default CUDA build plus several GB of nvidia-* packages neither of them
# actually uses here (this host runs CPU inference only). Installing the CPU wheel
# first satisfies that dependency before pip ever considers the GPU one.
RUN pip install --no-cache-dir torch torchvision --index-url https://download.pytorch.org/whl/cpu
# .[ai]: the live evidence endpoint (app/services/retrieval.py) needs
# sentence-transformers at runtime now, not just for the one-off embedding scripts —
# same reasoning as scikit-learn moving to core deps in Week 4 for classification.
# Install the dependency set only (hatchling needs the package dir to exist to build).
RUN mkdir -p /app/backend/app && touch /app/backend/app/__init__.py \
    && pip install --no-cache-dir "/app/backend[ai]" \
    && pip uninstall -y ticketsense-backend

COPY backend/alembic.ini backend/docker-entrypoint.sh ./backend/
COPY backend/app ./backend/app

COPY ai ./ai
COPY db ./db
COPY data/kb ./data/kb

WORKDIR /app/backend
RUN chmod +x docker-entrypoint.sh

EXPOSE 8000
CMD ["./docker-entrypoint.sh"]
