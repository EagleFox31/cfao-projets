"""Tests : base SQLite en memoire, mode autonome, aucun service exterieur."""
import os

os.environ.setdefault("DEBUG", "True")
os.environ.setdefault("DEPLOYMENT_MODE", "standalone")

from .base import *  # noqa: E402,F401,F403

DEBUG = True
DEPLOYMENT_MODE = "standalone"
DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}}
CERBOS_HTTP = "http://cerbos.invalid:3592"
PLATFORM_CORE_URL = "http://core.invalid"
# Independant du .env du poste : les tests d'origine couvrent le module (8094, 5178)
# et le portail de la plateforme (5173 dev, 5174 servi).
ORIGINES_AUTORISEES = [
    "http://localhost:8094", "http://127.0.0.1:8094",
    "http://localhost:5178", "http://127.0.0.1:5178",
    "http://localhost:5173", "http://127.0.0.1:5173",
    "http://localhost:5174", "http://127.0.0.1:5174",
]
