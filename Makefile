# Gestionnaire de projets — commandes courantes.
# `test` et `policy-test` tournent sans Docker si Python / le binaire cerbos
# sont installes ; les autres cibles pilotent docker compose.
.PHONY: help up down logs test policy-test migrate shell synchroniser recap

CERBOS ?= cerbos
CERBOS_IMAGE := ghcr.io/cerbos/cerbos:0.40.0

help:
	@echo "  make up           - Construit et demarre le service seul (mode autonome)"
	@echo "  make down         - Arrete les conteneurs"
	@echo "  make logs         - Journaux en continu"
	@echo "  make test         - Tests de l'API (pytest, SQLite en memoire) et de l'interface (Vitest)"
	@echo "  make policy-test  - Compile et teste les regles Cerbos"
	@echo "  make migrate      - Applique les migrations dans le conteneur"
	@echo "  make shell        - Shell Django dans le conteneur"
	@echo "  make synchroniser - Lit une fois les depots GitHub de tous les projets"
	@echo "  make recap        - Envoie le recapitulatif hebdomadaire aux chefs de projet"

up:
	docker compose up -d --build

down:
	docker compose down

logs:
	docker compose logs -f

test:
	cd api && python -m pytest -q
	cd web && npm test

# Binaire local s'il existe, sinon l'image officielle.
policy-test:
	@if command -v $(CERBOS) >/dev/null 2>&1; then \
		$(CERBOS) compile --tests=cerbos/tests cerbos/policies; \
	else \
		MSYS_NO_PATHCONV=1 docker run --rm -v "$(CURDIR)/cerbos:/work" $(CERBOS_IMAGE) \
			compile --tests=/work/tests /work/policies; \
	fi

migrate:
	docker compose exec api python manage.py migrate

shell:
	docker compose exec api python manage.py shell

synchroniser:
	docker compose exec api python manage.py synchroniser_github

recap:
	docker compose exec api python manage.py recap_hebdo
