# Cerbos du module avec ses politiques embarquees : en prod, rien n'est monte
# depuis le disque du serveur. Contexte de build : cfao-comptes-rendus/cerbos/.
FROM ghcr.io/cerbos/cerbos:0.40.0

COPY policies /policies
COPY config.yaml /config/config.yaml

CMD ["server", "--config=/config/config.yaml"]
