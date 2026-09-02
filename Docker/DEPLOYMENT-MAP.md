# Deployment Map

Agent container menjalankan `fraudguard_agent.main:app` pada port 3000 dan dipublish
hanya ke loopback host. Ia tidak memiliki volume database.

Development:

```bash
docker compose -f Docker/compose.yaml up --build
```

Production menggunakan `Docker/compose.production.yaml` dan `.env.production` dengan
Core HTTPS URL, scoped Core API key, serta agent client key. Reverse proxy publik hanya
boleh meneruskan endpoint agent setelah autentikasi.

```bash
cp Docker/docker.env.example .env.production
# Replace every placeholder before continuing.
docker compose -f Docker/compose.production.yaml up -d --build
curl http://127.0.0.1:3000/health
curl http://127.0.0.1:3000/ready
```

OpenClaw pada host menggunakan `http://127.0.0.1:3000`. OpenClaw di container terpisah
memerlukan shared network atau authenticated HTTPS proxy; container tersebut tidak dapat
memakai loopback milik host secara langsung.
