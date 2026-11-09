"""Configuration du module « gestionnaire de projets » (cfao-projets).

Reprend celle du kit `template-service` de la plateforme CFAO Academy :
base propre au module, mode `standalone` (developpement), `local` (reseau
interne, comptes a mot de passe) ou `integrated` (identites Keycloak de la
plateforme), PDP Cerbos. S'y ajoutent la lecture GitHub et le courrier.
"""
import os
from pathlib import Path

import environ
from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Ne vaut que pour le poste de dev : les modes local et integre la refusent.
CLE_DE_DEV = "cle-de-dev-non-secrete"

env = environ.Env(
    DEBUG=(bool, False),
    DEPLOYMENT_MODE=(str, "standalone"),
    SECRET_KEY=(str, CLE_DE_DEV),
    CERBOS_HTTP=(str, "http://localhost:3592"),
    PLATFORM_CORE_URL=(str, "http://localhost:8000"),
    OIDC_ISSUER=(str, ""),
    OIDC_AUDIENCE=(str, ""),
    OIDC_JWKS_URL=(str, ""),
    OIDC_CONNEXION=(str, "/oauth2/start?rd=/portail"),
    OIDC_DECONNEXION=(str, "/oauth2/sign_out?rd=/"),
    PROFILS_LOCAUX=(str, str(BASE_DIR / "profils-locaux.json")),
    COMPTES_LOCAUX=(str, ""),
    COOKIE_SESSION=(str, "cfao_pj_session"),
    COOKIE_SECURE=(bool, False),
    # Adresse publique du module, dans les liens des courriels.
    PJ_URL_PUBLIQUE=(str, "http://localhost:8094"),
    # Lecture GitHub : jeton par defaut (lecture seule suffit), API et secret des webhooks.
    GITHUB_TOKEN=(str, ""),
    GITHUB_API_URL=(str, "https://api.github.com"),
    GITHUB_WEBHOOK_SECRET=(str, ""),
    SYNCHRO_RECOUVREMENT_HEURES=(int, 72),
    # Courrier : `hub` (cfao-academy-mail), `smtp`, `console` (journal) ou `aucun`.
    MAIL_MODE=(str, "console"),
    MAIL_HUB_URL=(str, "http://mail-api:8000"),
    MAIL_HUB_KEY=(str, ""),
    MAIL_SMTP_HOST=(str, ""),
    MAIL_SMTP_PORT=(int, 25),
    MAIL_SMTP_USER=(str, ""),
    MAIL_SMTP_PASSWORD=(str, ""),
    MAIL_SMTP_TLS=(bool, False),
    MAIL_FROM=(str, "CFAO Academy <helpdeskcm@cfao.com>"),
    MAIL_PREFIX=(str, "[CFAO Academy]"),
)

environ.Env.read_env(os.path.join(BASE_DIR.parent, ".env"))

SECRET_KEY = env("SECRET_KEY")
DEBUG = env("DEBUG")
DEPLOYMENT_MODE = env("DEPLOYMENT_MODE")
CERBOS_HTTP = env("CERBOS_HTTP")
PLATFORM_CORE_URL = env("PLATFORM_CORE_URL")

if DEPLOYMENT_MODE not in ("standalone", "local", "integrated"):
    raise ImproperlyConfigured("DEPLOYMENT_MODE : 'standalone', 'local' ou 'integrated'.")
# Le mode autonome identifie sans mot de passe : il ne sert qu'au poste de dev.
if DEPLOYMENT_MODE == "standalone" and not DEBUG:
    raise ImproperlyConfigured("DEPLOYMENT_MODE=standalone exige DEBUG=True (developpement seulement).")

# Identite OIDC (Keycloak) : jeton Bearer verifie par les cles JWKS.
OIDC_ISSUER = env("OIDC_ISSUER")
OIDC_AUDIENCE = env("OIDC_AUDIENCE")
OIDC_JWKS_URL = env("OIDC_JWKS_URL")
# Ou envoyer le navigateur pour se connecter / se deconnecter (oauth2-proxy).
OIDC_CONNEXION = env("OIDC_CONNEXION")
OIDC_DECONNEXION = env("OIDC_DECONNEXION")

# Le mode integre est expose : il refuse de demarrer sans vraie cle ni
# emetteur OIDC, plutot que de tourner avec une configuration de dev.
if DEPLOYMENT_MODE == "integrated":
    _manquants = [nom for nom, valeur in (("SECRET_KEY", SECRET_KEY != CLE_DE_DEV and SECRET_KEY),
                                          ("OIDC_ISSUER", OIDC_ISSUER),
                                          ("OIDC_AUDIENCE", OIDC_AUDIENCE),
                                          ("OIDC_JWKS_URL", OIDC_JWKS_URL)) if not valeur]
    if _manquants:
        raise ImproperlyConfigured("Mode integre : a renseigner : " + ", ".join(_manquants) + ".")
# Profils fictifs du mode autonome (aucun vrai nom dans le depot).
PROFILS_LOCAUX = env("PROFILS_LOCAUX")
# Mode local : empreintes des mots de passe (base SQLite hors depot).
COMPTES_LOCAUX = env("COMPTES_LOCAUX")

# Le mode local est expose au reseau interne : vraie cle, mots de passe,
# et jamais DEBUG (les pages d'erreur detaillees montreraient la configuration).
if DEPLOYMENT_MODE == "local":
    _manquants = [nom for nom, valeur in (("SECRET_KEY", SECRET_KEY != CLE_DE_DEV and SECRET_KEY),
                                          ("COMPTES_LOCAUX", COMPTES_LOCAUX)) if not valeur]
    if _manquants:
        raise ImproperlyConfigured("Mode local : a renseigner : " + ", ".join(_manquants) + ".")
    if DEBUG:
        raise ImproperlyConfigured("DEPLOYMENT_MODE=local exige DEBUG=False.")

# Cookie de session : meme hote, ports differents = meme site, donc un nom
# propre au module evite de croiser le cookie d'une autre application ;
# `Secure` s'active derriere HTTPS (COOKIE_SECURE=True).
COOKIE_SESSION = env("COOKIE_SESSION")
COOKIE_SECURE = env("COOKIE_SECURE")

# Origines des pages autorisees a ecrire (POST/PUT/PATCH/DELETE) avec le
# cookie de session : passerelle du module et serveur de dev de l'interface.
ORIGINES_AUTORISEES = [o.rstrip("/") for o in env.list("ORIGINES_AUTORISEES", default=[
    "http://localhost:8094", "http://127.0.0.1:8094",
    "http://localhost:5178", "http://127.0.0.1:5178",
    # Portail de la plateforme (dev 5173, servi 5174) : il appelle le module par son proxy.
    "http://localhost:5173", "http://127.0.0.1:5173",
    "http://localhost:5174", "http://127.0.0.1:5174"])]

# Les noms sous lesquels le service est appele (passerelle : son nom public).
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=["localhost", "127.0.0.1"])

INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.auth",
    "rest_framework",
    "core",
    "projets",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.middleware.common.CommonMiddleware",
    "core.middleware.ControleOrigine",
    "projets.erreurs.Intercepteur",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"

DATABASES = {
    "default": env.db("DATABASE_URL", default="sqlite:///db.sqlite3")
}
# SQLite ignore `select_for_update` : chaque transaction prend le verrou
# d'ecriture des son debut (deux decisions simultanees sur une proposition
# liraient le meme etat). L'attente evite un « database is locked » immediat.
if DATABASES["default"]["ENGINE"] == "django.db.backends.sqlite3":
    DATABASES["default"].setdefault("OPTIONS", {}).update(
        {"transaction_mode": "IMMEDIATE", "timeout": 20})

CACHES = {"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}

LANGUAGE_CODE = "fr-fr"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
# Routes sans barre finale, comme les autres modules de la plateforme.
APPEND_SLASH = False

_AUTHENTIFICATION = {
    "integrated": "core.auth.oidc.KeycloakJWTAuthentication",
    "standalone": "core.auth.locale.LocaleAuthentication",
    "local": "core.auth.locale.LocaleAuthentication",
}

REST_FRAMEWORK = {
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
    ],
    "DEFAULT_PARSER_CLASSES": [
        "rest_framework.parsers.JSONParser",
    ],
    "DEFAULT_AUTHENTICATION_CLASSES": [_AUTHENTIFICATION[DEPLOYMENT_MODE]],
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticated"],
    "UNAUTHENTICATED_USER": None,
    "EXCEPTION_HANDLER": "core.exceptions.erreur_en_francais",
}

# ── Lecture GitHub ────────────────────────────────────────────────────
GITHUB_TOKEN = env("GITHUB_TOKEN")
GITHUB_API_URL = env("GITHUB_API_URL").rstrip("/")
GITHUB_WEBHOOK_SECRET = env("GITHUB_WEBHOOK_SECRET")
# Heures relues en arriere a chaque synchronisation (commits pousses en retard).
SYNCHRO_RECOUVREMENT_HEURES = env("SYNCHRO_RECOUVREMENT_HEURES")

# ── Courrier ──────────────────────────────────────────────────────────
MAIL_MODE = env("MAIL_MODE")
if MAIL_MODE not in ("hub", "smtp", "console", "aucun"):
    raise ImproperlyConfigured("MAIL_MODE : 'hub', 'smtp', 'console' ou 'aucun'.")
MAIL_HUB_URL = env("MAIL_HUB_URL").rstrip("/")
MAIL_HUB_KEY = env("MAIL_HUB_KEY")
if MAIL_MODE == "hub" and not MAIL_HUB_KEY:
    raise ImproperlyConfigured("MAIL_MODE=hub exige MAIL_HUB_KEY (cle de service du hub).")
MAIL_FROM = env("MAIL_FROM")
MAIL_PREFIX = env("MAIL_PREFIX")
PJ_URL_PUBLIQUE = env("PJ_URL_PUBLIQUE").rstrip("/")
EMAIL_HOST = env("MAIL_SMTP_HOST")
EMAIL_PORT = env("MAIL_SMTP_PORT")
EMAIL_HOST_USER = env("MAIL_SMTP_USER")
EMAIL_HOST_PASSWORD = env("MAIL_SMTP_PASSWORD")
EMAIL_USE_TLS = env("MAIL_SMTP_TLS")
DEFAULT_FROM_EMAIL = MAIL_FROM
if MAIL_MODE == "smtp" and not EMAIL_HOST:
    raise ImproperlyConfigured("MAIL_MODE=smtp exige MAIL_SMTP_HOST.")

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "root": {"handlers": ["console"], "level": "INFO"},
}
