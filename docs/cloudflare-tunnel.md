# Cloudflare Tunnel Setup

Zero-trust ingress for all internal services.
No open ports. No Nginx config. No Let's Encrypt.
Cloudflare terminates TLS at the edge and tunnels traffic to containers.

## Architecture

```
Browser
  │ HTTPS (Cloudflare terminates TLS)
  ▼
Cloudflare Edge
  │ Encrypted outbound tunnel
  ▼
cloudflared container (on VPS)
  │ Internal Docker network
  ▼
Target container (dockge:5001, grafana:3000, etc.)
```

No inbound ports open on VPS. VPS firewall can block 80 and 443 entirely.

---

## One-time setup (Cloudflare dashboard)

### 1. Create the tunnel

1. Go to [one.dash.cloudflare.com](https://one.dash.cloudflare.com)
2. Networks → Tunnels → **Create a tunnel**
3. Name: `autonomyx-gateway`
4. Select **Docker** as connector type
5. Copy the token from the `docker run` command shown
6. Add as GitHub Secret: `CLOUDFLARE_TUNNEL_TOKEN`

### 2. Add public hostnames (in the tunnel config)

After creating the tunnel, go to **Public Hostnames** tab and add:

| Subdomain | Domain | Service |
|---|---|---|
| `dockge` | openautonomyx.com | `http://dockge:5001` |
| `metrics` | openautonomyx.com | `http://grafana:3000` |
| `errors` | openautonomyx.com | `http://glitchtip:8080` |
| `flows` | openautonomyx.com | `http://langflow:7860` |
| `trust` | openautonomyx.com | `http://trust:80` |

> The service URL uses the Docker **container name** as hostname — containers
> on the same Docker network resolve each other by name.

### 3. Protect with Zero Trust Access (recommended)

For internal tools (Dockge, Grafana, GlitchTip):

1. Access → Applications → **Add an application** → Self-hosted
2. Application name: e.g. `Dockge`
3. Subdomain: `dockge.openautonomyx.com`
4. Add policy → **Emails** → `chinmay@openautonomyx.com`
5. Save

Now anyone hitting `dockge.openautonomyx.com` gets a Cloudflare login page
first. Only your email can authenticate.

### 4. Push to deploy

```bash
gh secret set CLOUDFLARE_TUNNEL_TOKEN \
  --repo OpenAutonomyx/autonomyx-model-gateway
git push origin main   # CI injects token and starts cloudflared
```

---

## Services exposed via tunnel

| URL | Internal service | Zero Trust |
|---|---|---|
| `dockge.openautonomyx.com` | dockge:5001 | ✅ Email auth |
| `metrics.openautonomyx.com` | grafana:3000 | ✅ Email auth |
| `errors.openautonomyx.com` | glitchtip:8080 | ✅ Email auth |
| `flows.openautonomyx.com` | langflow:7860 | ✅ Email auth |
| `trust.openautonomyx.com` | trust:80 | Public |
| `llm.openautonomyx.com` | litellm:4000 | API key auth |

---

## What Traefik still handles

Traefik remains in the stack for internal routing between containers.
Cloudflare Tunnel replaces the need to expose Traefik ports externally.

You can optionally close ports 80 and 443 on the OVH firewall entirely
once the tunnel is working — the VPS only needs port 22 (SSH) open.

```bash
# After confirming tunnel works:
ufw delete allow 80
ufw delete allow 443
ufw status  # should show only SSH allowed
```

---

## Troubleshooting

```bash
# Check tunnel status
docker logs autonomyx-cloudflared

# Verify tunnel is connected
docker exec autonomyx-cloudflared cloudflared tunnel info

# Test internal routing
docker exec autonomyx-cloudflared curl http://dockge:5001
```

If tunnel disconnects: check `CLOUDFLARE_TUNNEL_TOKEN` is set correctly in `.env`.
