# frp Tunnel Setup

Fast Reverse Proxy — Apache 2.0, no cloud, no vendor lock-in.
GitHub: https://github.com/fatedier/frp
25k+ stars, actively maintained since 2016.

## Architecture

```
Browser
  ↓ HTTPS (Traefik handles TLS via Let's Encrypt)
Traefik (port 443 on VPS)
  ↓ proxies to frps vhost port 80
frps (systemd service on host, port 7000 + 80)
  ↓ tunnel over localhost
frpc (Docker container, connects to host frps)
  ↓ Docker internal network
dockge:5001 / grafana:3000 / glitchtip:8080 / langflow:7860
```

frps and frpc run on the same VPS.
frpc connects outbound to frps — no new inbound ports needed beyond
what Traefik already uses (80 + 443).
frps listens on 7000 (frpc connection, internal only) and 80 (vhosts).

## Fully automated

`bootstrap_server.sh` handles everything on first deploy:
- Downloads frps binary from GitHub releases (v0.62.0)
- Installs to `/usr/local/bin/frps`
- Writes `/etc/frp/frps.toml` with `FRP_TOKEN` substituted
- Installs and starts `frps.service` via systemd

`frpc` runs as a Docker container, config at `frp/frpc.toml`.
`FRP_TOKEN` injected by CI from GitHub Secret.

## DNS required

Each subdomain needs an A record:

```
dockge.openautonomyx.com   A  51.75.251.56
metrics.openautonomyx.com  A  51.75.251.56
errors.openautonomyx.com   A  51.75.251.56
flows.openautonomyx.com    A  51.75.251.56
trust.openautonomyx.com    A  51.75.251.56
```

Or a wildcard: `*.openautonomyx.com A 51.75.251.56`

## Traefik routes to frps

Add these routes to Traefik config so it proxies to frps vhosts:

```yaml
# In Traefik dynamic config or as container labels on frpc:
http:
  routers:
    dockge:
      rule: "Host(`dockge.openautonomyx.com`)"
      service: frps-vhost
      tls:
        certResolver: letsencrypt
  services:
    frps-vhost:
      loadBalancer:
        servers:
          - url: "http://host-gateway:80"
```

frps receives the request on port 80 with the Host header intact
and routes it to the correct frpc proxy by subdomain.

## Services exposed

| URL | Internal service | Auth |
|---|---|---|
| `dockge.openautonomyx.com` | dockge:5001 | Dockge login |
| `metrics.openautonomyx.com` | grafana:3000 | Grafana login |
| `errors.openautonomyx.com` | glitchtip:8080 | GlitchTip login |
| `flows.openautonomyx.com` | langflow:7860 | Langflow login |
| `trust.openautonomyx.com` | trust:80 | Public |

Each service handles its own authentication — no extra auth layer needed
since all tools already have login pages.

## Troubleshooting

```bash
# Check frps status
systemctl status frps
journalctl -u frps -f

# Check frpc logs
docker logs autonomyx-frpc -f

# Verify frpc connected to frps
curl http://localhost:7500/api/proxy/http  # frps dashboard API

# Test internal routing
docker exec autonomyx-frpc wget -qO- http://dockge:5001
```

## Why frp over Pangolin/Cloudflare Tunnel

| | frp | Pangolin | Cloudflare Tunnel |
|---|---|---|---|
| License | Apache 2.0 | AGPL-3.0 | Proprietary |
| Cloud dependency | None | None (self-hosted) | Cloudflare |
| Company risk | None (no company) | YC startup | Cloudflare |
| Maturity | 2016, 25k stars | 2024, early | Mature |
| Config | TOML files | Web dashboard | CF dashboard |
| SSL | Via Traefik | Built-in | Built-in |
