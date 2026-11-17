---
title: VPS and agx64 gateway notes
updated: 2026-11-17
sources:
  - /mnt/knowledge/raxxar/00_System/sessions/2026-09-30.md
  - /mnt/knowledge/raxxar/06_knowledge/architectures/real-life-dev-public-edge.md
  - /mnt/knowledge/raxxar/00_System/raxxar-cluster.md
  - live checks on megasrv and agx64, 2026-11-17
tags:
  - deployment
  - vps
  - wireguard
  - agx64
---

# VPS and agx64 gateway notes

Read-only discovery on 2026-11-17, followed by explicit gateway setup. No key
material, password or private configuration is stored in this page or the
repository.

## Public edge

- `real-life.dev` resolves to the netcup VPS `152.53.196.118`.
- SSH alias: `megasrv` (user `deploy`, port 22, key auth).
- Host: Debian 13, nginx active, IPv4 and IPv6 reachable, HTTPS 200.
- Capacity: 3.8 GiB RAM, 49 GiB free on `/`.
- Existing site: `/var/www/spark`, nginx site `real-life-dev`.
- The VPS cannot reach the home LAN (`192.168.178.0/24`) directly.

## agx64

- SSH alias: `agx64` (user `raxxar`, host `192.168.178.21`).
- Ubuntu 20.04.6 LTS; Ollama listens on `*:11434` at the host level.
- The host kernel has no WireGuard module, so the gateway uses the
  `wireguard-go` userspace fallback and a small `wg0-agx64.service`.
- The existing `wg1` Sparknet overlay is separate and must not be disturbed.
- The existing developer path is still an SSH tunnel to `127.0.0.1:21464/v1`.

## Gateway implementation

```text
Streamlit Cloud --HTTPS--> https://real-life.dev/v1
                                |
                                v
                         megasrv nginx :443
                         bearer-token check + rate limit
                                |
                                v
                         WireGuard 10.66.0.1
                                |
                        10.66.0.2:11434
                                |
                              agx64 Ollama
```

- VPS `wg0`: `10.66.0.1/24`; agx64 `wg0`: `10.66.0.2/24`.
- agx64 initiates the handshake with `PersistentKeepalive = 25`; no home
  port-forward is required.
- UFW allows UDP 51820 and TCP 443. agx64 has no public inbound port.
- nginx exposes `GET /healthz`, `GET /v1/models`,
  `POST /v1/chat/completions` and `POST /v1/embeddings` only.
- `/healthz` is unauthenticated. The `/v1/*` endpoints require the
  server-side bearer token; `/api/*` is not proxied.
- The token is stored at `/etc/nginx/agx64-gateway-token` on the VPS and in
  Streamlit secrets/local `.env` as `LOCAL_API_KEY`. It is never committed.
- Rate limit: 30 requests/minute per client IP, burst 20.
- No direct `11434` or `/api/*` exposure.

## Verified on 2026-11-17 from this build host

- `wg show` reports a recent handshake between the VPS and `agx64`.
- VPS `ping -c 2 10.66.0.2` succeeds.
- `https://real-life.dev/healthz` returns `200`.
- `https://real-life.dev/v1/models` returns `401` without a token.
- The same endpoint returns `200` with the server-side bearer token.
- `https://real-life.dev/` still returns `200`.
- The Streamlit Cloud secret has **not** been verified from this host; that is
  an owner action.

## User action: wire the Cloud app

In Streamlit Cloud app settings, add:

```toml
LOCAL_BASE_URL = "https://real-life.dev/v1"
LOCAL_API_KEY = "the server-side gateway token"
```

Do not put the token in the repository, a page or a chat message. After saving,
click **Discover agx64 models** in the app and then select an `agx64` model; a failure
must stay local and must not fall back to OpenRouter.

## Operations

- VPS: `sudo systemctl status nginx`, `sudo wg show`, `sudo ufw status`.
- Repeatable check: `LOCAL_API_KEY=... ./scripts/smoke_gateway.sh` from the
  project; it never prints the token.
- agx64: `sudo systemctl status wg0-agx64`, `sudo wg show wg0`,
  `ip -4 addr show wg0`.
- nginx config: `/etc/nginx/snippets/agx64-gateway.conf` and
  `/etc/nginx/conf.d/agx64-gateway-map.conf`; site backup:
  `/etc/nginx/sites-available/real-life-dev.pre-agx64-2026-11-17`.
- Token rotation: replace `/etc/nginx/agx64-gateway-token`, update the token in
  the map file and Streamlit secrets, run `sudo nginx -t && sudo systemctl
  reload nginx`. Never print the token.
- Rollback: restore the site backup, remove the gateway snippet/map, reload
  nginx; disable `wg0-agx64` on agx64 and `wg-quick@wg0` on the VPS.

## Boundaries

- The `real-life.dev` project card remains suspended. This is infrastructure,
  not a marketing card.
- No live Cloud-to-gateway claim is made until the owner confirms the Cloud
  secret and a model call.
