---
title: VPS and agx64 gateway notes
updated: 2026-11-17
sources:
  - /mnt/knowledge/raxxar/00_System/sessions/2026-09-30.md
  - /mnt/knowledge/raxxar/06_knowledge/architectures/real-life-dev-public-edge.md
  - /mnt/knowledge/raxxar/00_System/raxxar-cluster.md
tags:
  - deployment
  - vps
  - wireguard
  - agx64
---

# VPS and agx64 gateway notes

Read-only discovery on 2026-11-17. No key material, password or private
configuration was read.

## Public edge

- `real-life.dev` resolves to the netcup VPS `152.53.196.118`.
- SSH alias: `megasrv` (user `deploy`, port 22, key auth).
- Host: Debian 13, nginx active, IPv4 and IPv6 reachable, HTTPS 200.
- Capacity: 3.8 GiB RAM, 49 GiB free on `/`.
- Existing site: `/var/www/spark`, nginx site `real-life-dev`.
- The site has a self-hosted git remote; the current `main` observed during
  discovery was `abdffb8`.
- No WireGuard service is active on the VPS.
- The VPS cannot reach the home LAN (`192.168.178.0/24`).

## agx64

- SSH alias: `agx64` (user `raxxar`, host `192.168.178.21`).
- Ubuntu 20.04.6 LTS; Ollama is exposed on `*:11434` at the host level.
- The interactive Serve app is not on agx64; this is the model endpoint only.
- The existing developer path is an SSH tunnel to `127.0.0.1:21464/v1`.
- The public app cannot use that tunnel. It needs the VPS gateway below.

## Gateway design (proposed)

```text
Streamlit Cloud --HTTPS--> https://<gateway-host>/v1
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
- VPS opens only UDP 51820 and TCP 443; agx64 has no public inbound port.
- nginx allows only `GET /v1/models`, `POST /v1/chat/completions` and
  `POST /v1/embeddings`; `GET /healthz` is unauthenticated.
- The app uses `LOCAL_BASE_URL=https://<gateway-host>/v1` and a
  `LOCAL_API_KEY` stored only in the project `.env` or Streamlit secrets.
- No silent fallback: if the gateway is down, the `agx64` option shows an
  error; it does not send the prompt to OpenRouter.
- The `real-life.dev` project card stays suspended. This is infrastructure,
  not a marketing card.

## Open actions

- Choose the gateway hostname (for example `agx64.real-life.dev`).
- Add the DNS record and certificate.
- Apply the WireGuard and nginx config with a console fallback open.
- Verify 401/200, `/healthz`, `wg show`, and a real model response from the
  Streamlit Cloud app.
