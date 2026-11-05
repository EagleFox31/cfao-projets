#!/usr/bin/env bash
set -euo pipefail

# ==============================================================================
# CFAO Projets - deploiement (images Docker Hub) avec detection d'hote LAN
#   ./deploy.sh [docker-compose.prod.yml]
# Les valeurs du .env priment ; a defaut, le module est servi en HTTP sur le LAN.
# ==============================================================================

COMPOSE_FILE="${1:-docker-compose.prod.yml}"
ENV_FILE="${ENV_FILE:-.env}"
touch "$ENV_FILE"

env_value() {
  sed -n "s/^$1=//p" "$ENV_FILE" | tr -d '\r' | tail -n 1
}

# 1. Secrets : generes une seule fois puis conserves dans le .env (la base
#    est initialisee avec ce mot de passe, il ne doit plus changer).
for cle in SECRET_KEY POSTGRES_PASSWORD; do
  if [ -z "$(env_value $cle)" ]; then
    echo "$cle=$(head -c 48 /dev/urandom | base64 | tr -d '/+=\n' | head -c 50)" >> "$ENV_FILE"
    echo "[deploy] $cle genere dans $ENV_FILE"
  fi
done

# 2. Hote LAN
PJ_LAN_HOST="${PJ_LAN_HOST:-$(env_value PJ_LAN_HOST)}"
if [ -z "$PJ_LAN_HOST" ]; then
  PJ_LAN_HOST=$(ip -4 route get 1.1.1.1 2>/dev/null \
    | awk '{for(i=1;i<=NF;i++) if($i=="src") print $(i+1)}' | head -n1 || true)
  PJ_LAN_HOST="${PJ_LAN_HOST:-$(hostname -I 2>/dev/null | awk '{print $1}' || true)}"
  PJ_LAN_HOST="${PJ_LAN_HOST:-localhost}"
fi

# 3. Port, liaison et URL publique : .env > valeurs LAN
PJ_PORT="${PJ_PORT:-$(env_value PJ_PORT)}"; export PJ_PORT="${PJ_PORT:-8094}"
PJ_BIND="${PJ_BIND:-$(env_value PJ_BIND)}"; export PJ_BIND="${PJ_BIND:-0.0.0.0}"
PJ_PUBLIC_URL="${PJ_PUBLIC_URL:-$(env_value PJ_PUBLIC_URL)}"
PJ_PUBLIC_URL="${PJ_PUBLIC_URL:-http://${PJ_LAN_HOST}:${PJ_PORT}}"; export PJ_PUBLIC_URL
HOTE_PUBLIC=$(echo "$PJ_PUBLIC_URL" | sed -E 's#^[a-z]+://##; s#[:/].*$##')

ORIGINES_AUTORISEES="${ORIGINES_AUTORISEES:-$(env_value ORIGINES_AUTORISEES)}"
export ORIGINES_AUTORISEES="${ORIGINES_AUTORISEES:-${PJ_PUBLIC_URL},http://localhost:${PJ_PORT}}"
ALLOWED_HOSTS="${ALLOWED_HOSTS:-$(env_value ALLOWED_HOSTS)}"
export ALLOWED_HOSTS="${ALLOWED_HOSTS:-${HOTE_PUBLIC},localhost,127.0.0.1}"
COOKIE_SECURE="${COOKIE_SECURE:-$(env_value COOKIE_SECURE)}"
if [ -z "$COOKIE_SECURE" ]; then
  case "$PJ_PUBLIC_URL" in https://*) COOKIE_SECURE=True ;; *) COOKIE_SECURE=False ;; esac
fi
export COOKIE_SECURE

echo "=========================================================="
echo " CFAO Projets - Deploiement Conteneurs"
echo "=========================================================="
echo " Fichier Compose  : $COMPOSE_FILE"
echo " Fichier d'env    : $ENV_FILE"
echo " Hote LAN         : $PJ_LAN_HOST"
echo " URL publique     : $PJ_PUBLIC_URL"
echo " Origines         : $ORIGINES_AUTORISEES"
echo " Cookie Secure    : $COOKIE_SECURE"
echo "=========================================================="

docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" pull
docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" up -d
