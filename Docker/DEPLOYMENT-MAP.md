# Deployment Map

Compose menjalankan dua proses dengan image yang sama:

- `agent` menjalankan typed tool adapter `fraudguard_agent.main:app` pada loopback port
  `3000`; OpenClaw TUI/admin dapat memanggil endpoint ini melalui CLI terikat.
- `bridge` menjalankan `fraudguard_agent.openclaw_bridge:app` pada port `3100`; alias
  network `fraudguard-agent` dan Caddy `/agent/*` hanya menunjuk proses ini. Bridge
  menyediakan typed client tools pada OpenResponses dan meneruskan function call ke Core.

Keduanya tidak memiliki volume database. OpenClaw Gateway tetap private pada host dan
diakses bridge melalui `host.docker.internal:18789` dengan bearer token server-side.

Core dan Agent memakai external network `fraudguard-network`. Script deployment membuat
network tersebut bila belum ada, sehingga kedua repository boleh berada di path VPS mana
pun.

Deployment:

```bash
cp .env.example .env
./deploy.sh deploy
```

Production dapat menggunakan `.env.production` dengan Core HTTPS URL atau alias internal
`http://fraudguard-core-api:8000/api/v1`, scoped Core API key, serta agent client key.
Reverse proxy publik hanya boleh meneruskan endpoint agent setelah autentikasi.

```bash
cp Docker/docker.env.example .env.production
# Replace every placeholder before continuing.
openclaw config set gateway.http.endpoints.responses.enabled true
DOCKER_HOST_GATEWAY="$(docker network inspect bridge --format '{{(index .IPAM.Config 0).Gateway}}')"
openclaw config set gateway.bind custom
openclaw config set gateway.customBindHost "$DOCKER_HOST_GATEWAY"
openclaw gateway restart
ENV_FILE=.env.production ./deploy.sh deploy
curl http://127.0.0.1:3000/health
curl -H "X-Agent-Key: $AGENT_ACCESS_KEY" http://127.0.0.1:3100/ready
```

OpenClaw TUI/admin pada host dapat menggunakan CLI ke `http://127.0.0.1:3000`. Browser tidak menerima
Gateway token, Core API key, atau tool-adapter key; browser hanya memakai same-origin
`/agent/v1/chat` yang diteruskan Caddy ke bridge.

Jangan bind Gateway ke `lan`/`0.0.0.0`. Bind `custom` ke Docker host gateway menjaga
port 18789 pada jalur host/container private; firewall publik tetap harus menolak port itu.

Gunakan `./deploy.sh update` untuk fast-forward pull, rebuild, dan recreate;
`./deploy.sh restart` hanya merestart container yang sudah ada.
