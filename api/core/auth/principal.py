"""Le « principal » : qui agit, avec quels roles et quel perimetre.

Construit a partir de ce que renvoie l'adaptateur d'identite
(`identity.py`), jamais a partir d'un en-tete choisi par le navigateur
en mode integre.
"""
from __future__ import annotations

from dataclasses import dataclass, field

# Champs d'affichage repris tels quels dans le profil renvoye au portail.
CHAMPS_AFFICHAGE = ("firstName", "lastName", "email", "locale", "pays", "filiale",
                    "orgLabel", "orgPath", "departments", "instructorBrands")


@dataclass
class Principal:
    id: str
    roles: list[str] = field(default_factory=list)
    attr: dict = field(default_factory=dict)
    profil: dict = field(default_factory=dict)

    # DRF traite cet objet comme request.user.
    @property
    def is_authenticated(self) -> bool:
        return True

    def to_cerbos(self) -> dict:
        """Principal au format attendu par Cerbos."""
        return {"id": self.id, "roles": self.roles or ["_anon"], "attr": self.attr}

    def profil_portail(self) -> dict:
        """Le profil que le portail affiche (`/pj-donnees/session`)."""
        return {**self.profil, "id": self.id, "roles": self.roles,
                "scopeNodes": self.attr.get("scopeNodes", []),
                "brands": self.attr.get("brands", []), "compte": True}


def construire_principal(resolu: dict, claims: dict | None = None) -> Principal:
    """Principal a partir du perimetre resolu, et des claims du jeton s'il y en a.

    Les roles et le perimetre viennent toujours de `resolu` (source de
    verite : profil local ou `GET /api/v1/core/me`) ; les claims ne
    fournissent que les champs d'affichage absents.
    """
    claims = claims or {}
    scope_nodes = list(resolu.get("scopeNodes") or [])
    attr = {
        "scopeNodes": scope_nodes,
        # Exige par le schema du principal (cerbos/policies/_schemas).
        "scopeNode": scope_nodes[0] if scope_nodes else "",
        "brands": list(resolu.get("brands") or []),
        "departments": list(resolu.get("departments") or []),
    }
    profil = {k: resolu[k] for k in CHAMPS_AFFICHAGE if k in resolu}
    for cle, claim in (("firstName", "given_name"), ("lastName", "family_name"), ("email", "email")):
        if cle not in profil and claims.get(claim):
            profil[cle] = claims[claim]
    return Principal(id=str(resolu["id"]), roles=list(resolu.get("roles") or []),
                     attr=attr, profil=profil)
