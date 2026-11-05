"""Compte de l'equipe technique cree au deploiement (mode local)."""
import json
from pathlib import Path

import pytest
from django.core.management import call_command

from core.auth import comptes
from core.auth.identity import profil_local

IDENTIFIANT = "technique@exemple.test"
MOT_DE_PASSE = "Mdp-de-test-2026"


@pytest.fixture
def local(settings, tmp_path, monkeypatch):
    settings.DEPLOYMENT_MODE = "local"
    settings.COMPTES_LOCAUX = str(tmp_path / "comptes.sqlite")
    settings.PROFILS_LOCAUX = str(tmp_path / "profils.json")
    (tmp_path / "profils.json").write_text(json.dumps([{"identifiant": "f.demo", "id": "f-demo"}]))
    monkeypatch.setattr(comptes, "_echecs", {})
    monkeypatch.setenv("PJ_COMPTE_TECHNIQUE", IDENTIFIANT)
    monkeypatch.setenv("PJ_COMPTE_TECHNIQUE_MDP", MOT_DE_PASSE)
    return tmp_path


def test_le_compte_technique_est_cree_superadmin(local):
    call_command("compte_technique")
    profil = profil_local(IDENTIFIANT)
    assert profil["roles"] == ["superadmin"] and profil["id"] == "equipe.technique"
    assert profil_local("f.demo")
    assert comptes.verifier(IDENTIFIANT, MOT_DE_PASSE)


def test_un_mot_de_passe_change_survit_au_deploiement(local):
    call_command("compte_technique")
    comptes.changer_mot_de_passe(IDENTIFIANT, "nouveau1")
    call_command("compte_technique")
    assert comptes.verifier(IDENTIFIANT, "nouveau1")
    profils = json.loads((local / "profils.json").read_text())
    assert [p["identifiant"] for p in profils].count(IDENTIFIANT) == 1


def test_rien_hors_du_mode_local(local, settings):
    settings.DEPLOYMENT_MODE = "standalone"
    call_command("compte_technique")
    assert not profil_local(IDENTIFIANT)


@pytest.mark.parametrize("variable", ["PJ_COMPTE_TECHNIQUE", "PJ_COMPTE_TECHNIQUE_MDP"])
def test_aucun_compte_sans_identifiants_fournis(local, monkeypatch, variable):
    monkeypatch.delenv(variable)
    call_command("compte_technique")
    assert not profil_local(IDENTIFIANT)
    assert json.loads((local / "profils.json").read_text()) == [{"identifiant": "f.demo", "id": "f-demo"}]


def test_aucun_identifiant_par_defaut_dans_le_code():
    # Garde-fou : un superadmin ne doit jamais avoir d'identifiants codes en dur.
    source = (Path(__file__).resolve().parents[1] / "management/commands/compte_technique.py").read_text()
    assert "@" not in source.split('"""', 2)[2]
