# Passerelle du module : construit l'interface (web/) puis la sert avec nginx,
# qui route /apercu et /pj-donnees vers l'API.
# Contexte de build : cfao-projets/ (voir docker-compose.yml).

FROM node:20-alpine AS web
WORKDIR /web
COPY web/package.json web/package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY web/ ./
RUN npm run build

FROM nginx:1.27-alpine
COPY gateway/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=web /web/dist /usr/share/nginx/html
EXPOSE 80
