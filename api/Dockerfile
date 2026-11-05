# API du gestionnaire de projets : projets, equipes, taches, lecture GitHub,
# propositions de modification et courriels.
# Contexte de build : ce dossier (`api/`). Voir README.md a la racine.

# -- Dependances Python, construites a part : l'image finale n'a ni pip ni cache.
FROM python:3.12-slim AS dependances
ENV PIP_NO_CACHE_DIR=1 PIP_DISABLE_PIP_VERSION_CHECK=1
RUN python -m venv /opt/venv
COPY requirements.txt /tmp/requirements.txt
RUN /opt/venv/bin/pip install -r /tmp/requirements.txt

# -- Image d'execution.
FROM python:3.12-slim

# curl sert au healthcheck de docker compose ; rien d'autre n'est installe.
RUN apt-get update \
 && apt-get install -y --no-install-recommends curl \
 && rm -rf /var/lib/apt/lists/*

# Utilisateur sans privilege ; /donnees recoit les comptes locaux et les profils.
RUN useradd --create-home --uid 1000 service \
 && mkdir -p /donnees \
 && chown service:service /donnees

COPY --from=dependances /opt/venv /opt/venv
WORKDIR /app
COPY --chown=service:service . /app/

ENV PATH=/opt/venv/bin:$PATH \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DJANGO_SETTINGS_MODULE=config.settings.base \
    PJ_DONNEES=/donnees

USER service
EXPOSE 5175

# Migrations puis compte technique (mode local) avant de servir. Le service
# `synchro` du compose reutilise cette image avec sa propre commande.
CMD ["sh", "-c", "python manage.py migrate --noinput && python manage.py compte_technique && exec gunicorn config.wsgi:application --bind 0.0.0.0:5175 --workers 2 --threads 4 --timeout 60 --access-logfile -"]
