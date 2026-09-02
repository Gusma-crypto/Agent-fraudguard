# Deployment Map

Agent container menjalankan `fraudguard_agent.main:app` pada port 3000 dan dipublish
hanya ke loopback host. Ia tidak memiliki volume database.

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
ENV_FILE=.env.production ./deploy.sh deploy
curl http://127.0.0.1:3000/health
curl http://127.0.0.1:3000/ready
```

OpenClaw pada host menggunakan `http://127.0.0.1:3000`. OpenClaw di container terpisah
memerlukan shared network atau authenticated HTTPS proxy; container tersebut tidak dapat
memakai loopback milik host secara langsung.

Gunakan `./deploy.sh update` untuk fast-forward pull, rebuild, dan recreate;
`./deploy.sh restart` hanya merestart container yang sudah ada.
