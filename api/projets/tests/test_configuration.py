"""Les modes integre et local refusent de demarrer avec une configuration de dev.

Chaque cas charge la configuration dans un processus a part : elle est
lue une seule fois par processus.
"""
import os
import subprocess
import sys
from pathlib import Path

import pytest

API = Path(__file__).resolve().parents[2]
INTEGRE = {"DEPLOYMENT_MODE": "integrated", "SECRET_KEY": "une-vraie-cle",
           "OIDC_ISSUER": "http://keycloak/realms/cfao", "OIDC_AUDIENCE": "cfao-projets",
           "OIDC_JWKS_URL": "http://keycloak/realms/cfao/protocol/openid-connect/certs"}


def charger(code="from django.conf import settings; print(settings.ALLOWED_HOSTS)", **variables):
    env = {k: v for k, v in os.environ.items()
           if k not in ("DEPLOYMENT_MODE", "SECRET_KEY", "OIDC_ISSUER", "OIDC_JWKS_URL", "OIDC_AUDIENCE",
                        "DEBUG", "ALLOWED_HOSTS", "COMPTES_LOCAUX")}
    env.update(variables, DJANGO_SETTINGS_MODULE="config.settings.base")
    return subprocess.run([sys.executable, "-c", code],
                          cwd=API, env=env, capture_output=True, text=True)


def test_le_mode_integre_complet_demarre():
    r = charger(**INTEGRE)
    assert r.returncode == 0, r.stderr
    assert r.stdout.strip() == "['localhost', '127.0.0.1']"


@pytest.mark.parametrize("manquant", ["SECRET_KEY", "OIDC_ISSUER", "OIDC_AUDIENCE", "OIDC_JWKS_URL"])
def test_le_mode_integre_exige_cle_et_emetteur(manquant):
    # Vide plutot qu'absente : un `.env` local ne la remplit pas.
    r = charger(**{**INTEGRE, manquant: ""})
    assert r.returncode != 0
    assert manquant in r.stderr


def test_le_mode_integre_refuse_la_cle_de_dev():
    r = charger(**{**INTEGRE, "SECRET_KEY": "cle-de-dev-non-secrete"})
    assert r.returncode != 0
    assert "SECRET_KEY" in r.stderr


def test_le_mode_autonome_exige_debug():
    r = charger(DEPLOYMENT_MODE="standalone", DEBUG="False")
    assert r.returncode != 0
    assert "DEBUG=True" in r.stderr


LOCAL = {"DEPLOYMENT_MODE": "local", "SECRET_KEY": "une-vraie-cle", "COMPTES_LOCAUX": "comptes.sqlite",
         "DEBUG": "False"}


def test_le_mode_local_complet_demarre():
    r = charger(**LOCAL)
    assert r.returncode == 0, r.stderr


@pytest.mark.parametrize("manquant", ["SECRET_KEY", "COMPTES_LOCAUX"])
def test_le_mode_local_exige_cle_et_comptes(manquant):
    r = charger(**{**LOCAL, manquant: ""})
    assert r.returncode != 0
    assert manquant in r.stderr


def test_le_mode_local_refuse_la_cle_de_dev_et_debug():
    assert "SECRET_KEY" in charger(**{**LOCAL, "SECRET_KEY": "cle-de-dev-non-secrete"}).stderr
    assert "DEBUG=False" in charger(**{**LOCAL, "DEBUG": "True"}).stderr


VERROU = """
import sqlite3, django
django.setup()
from django.db import connection, transaction
with transaction.atomic():
    connection.cursor().execute("select 1")
    autre = sqlite3.connect(connection.settings_dict["NAME"], timeout=0)
    try:
        autre.execute("create table t (x)")
        print("libre")
    except sqlite3.OperationalError:
        print("verrou")
"""


def test_une_transaction_sqlite_prend_le_verrou_d_ecriture_des_le_debut(tmp_path):
    # select_for_update ne fait rien sous SQLite : sans ce verrou, deux
    # envois du meme brouillon liraient la meme revision.
    base = (tmp_path / "db.sqlite3").as_posix()
    r = charger(VERROU, **LOCAL, DATABASE_URL=f"sqlite:///{base}")
    assert r.returncode == 0, r.stderr
    assert r.stdout.strip() == "verrou"
