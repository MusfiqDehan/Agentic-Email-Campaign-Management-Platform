# Deployment Guide — Email Campaign Management Platform

Production deployment on a VPS with Docker Compose, Nginx, and Cloudflare.

| Service | Domain |
|---------|--------|
| Backend API | `https://emailcampaign-api.musfiqdehan.com` |
| Frontend | `https://emailcampaign.musfiqdehan.com` |

---

## Architecture

```
Internet → Cloudflare (SSL) → VPS :443
                                 ├─ Nginx (reverse proxy)
                                 │   ├─ emailcampaign-api.* → backend (Daphne :8001)
                                 │   │   ├─ /ws/* → WebSocket proxy
                                 │   │   ├─ /static/* → volume (direct serve)
                                 │   │   └─ /media/* → volume (direct serve)
                                 │   └─ emailcampaign.* → frontend (Next.js :3001)
                                 │
                                 ├─ PostgreSQL :5432 (internal only)
                                 ├─ Redis :6379 (internal only)
                                 ├─ Celery Worker
                                 └─ Celery Beat
```

---

## Prerequisites

- VPS with Docker Engine and Docker Compose plugin installed
- Domain `musfiqdehan.com` managed via Cloudflare
- SSH access to the VPS

---

## Step 1: Cloudflare DNS Setup

1. Go to **Cloudflare Dashboard → DNS → Records**
2. Add two **A records** pointing to your VPS IP address:

   | Type | Name | Content | Proxy |
   |------|------|---------|-------|
   | A | `emailcampaign-api` | `<YOUR_VPS_IP>` | Proxied (orange) |
   | A | `emailcampaign` | `<YOUR_VPS_IP>` | Proxied (orange) |

3. Go to **SSL/TLS → Overview** → Set mode to **Full (Strict)**

4. Go to **SSL/TLS → Origin Server → Create Certificate**:
   - RSA 2048
   - Hostnames: `*.musfiqdehan.com`, `musfiqdehan.com`
   - Validity: 15 years
   - Save the **Origin Certificate** as `origin.pem`
   - Save the **Private Key** as `origin.key`

---

## Step 2: Clone & Configure on VPS

```bash
# SSH into your VPS
ssh user@<YOUR_VPS_IP>

# Clone the repository
git clone https://github.com/MusfiqDehan/Agentic-Email-Campaign-Management-Platform.git /opt/ecmp
cd /opt/ecmp
git checkout dev

# Create the .env file from the example
cp .env.example .env
nano .env   # Fill in all values — especially SECRET_KEY, passwords, API keys
```

### Generate secure secrets:

```bash
# Generate Django SECRET_KEY
python3 -c "import secrets; print(secrets.token_urlsafe(50))"

# Generate SIGNING_KEY
python3 -c "import secrets; print(secrets.token_urlsafe(50))"

# Generate strong passwords for DB and Redis
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

---

## Step 3: Place SSL Certificates

```bash
# Copy the Cloudflare Origin Certificate files to the server
mkdir -p /opt/ecmp/nginx/certs

# On your LOCAL machine, copy the downloaded cert files to the VPS:
scp origin.pem user@<YOUR_VPS_IP>:/opt/ecmp/nginx/certs/origin.pem
scp origin.key user@<YOUR_VPS_IP>:/opt/ecmp/nginx/certs/origin.key

# On the VPS, set proper permissions:
chmod 600 /opt/ecmp/nginx/certs/origin.key
chmod 644 /opt/ecmp/nginx/certs/origin.pem
```

---

## Step 4: Firewall Configuration

```bash
# Allow only SSH, HTTP, and HTTPS
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw --force enable
sudo ufw status
```

---

## Step 5: Build & Deploy

```bash
cd /opt/ecmp

# Build all images (this will take a few minutes on first run)
docker compose build --no-cache

# Start everything in detached mode
docker compose up -d

# Check all services are running
docker compose ps

# Watch logs (Ctrl+C to stop watching)
docker compose logs -f
```

---

## Step 6: Post-Deploy Verification

```bash
# Check backend health
curl -I https://emailcampaign-api.musfiqdehan.com/api/v1/healthz/

# Check frontend
curl -I https://emailcampaign.musfiqdehan.com

# Check Swagger UI
curl -I https://emailcampaign-api.musfiqdehan.com/api/v1/schemas/swagger-ui/

# Check Django admin
curl -I https://emailcampaign-api.musfiqdehan.com/admin/

# Run Django deployment checklist
docker compose exec backend python manage.py check --deploy
```

---

## Useful Commands

```bash
# View logs for a specific service
docker compose logs -f backend
docker compose logs -f nginx
docker compose logs -f frontend
docker compose logs -f celery

# Restart a specific service
docker compose restart backend

# Access Django management shell
docker compose exec backend python manage.py shell

# Create a superuser manually
docker compose exec backend python manage.py createsuperuser

# Run database migrations
docker compose exec backend python manage.py migrate

# Rebuild and restart after code changes
git pull origin dev
docker compose build --no-cache
docker compose up -d

# Stop all services
docker compose down

# Stop and remove ALL data (including database volumes)
docker compose down -v
```

---

## File Structure (Deployment)

```
/opt/ecmp/
├── .env                        # Production environment variables
├── .env.example                # Template for .env
├── docker-compose.yml          # Unified compose file
├── nginx/
│   ├── nginx.conf              # Nginx reverse proxy config
│   └── certs/
│       ├── origin.pem          # Cloudflare Origin Certificate
│       └── origin.key          # Cloudflare Origin Private Key
├── backend/                    # Django REST Framework API
│   ├── Dockerfile
│   ├── docker_entrypoint.sh
│   └── ...
└── frontend/                   # Next.js Frontend
    ├── Dockerfile
    └── ...
```

---

## Troubleshooting

### 502 Bad Gateway
- Check if backend is running: `docker compose ps`
- Check backend logs: `docker compose logs backend`
- Ensure database migration completed: `docker compose exec backend python manage.py migrate`

### WebSocket connection fails
- Verify Cloudflare is not stripping WebSocket headers (it shouldn't with proxy enabled)
- Check nginx logs: `docker compose logs nginx`
- Ensure `wss://` is used (not `ws://`) in the frontend env

### SSL certificate errors
- Ensure Cloudflare SSL mode is **Full (Strict)**
- Verify origin cert files are in `nginx/certs/` with correct permissions
- Check nginx logs for SSL errors: `docker compose logs nginx | grep SSL`

### Static files not loading
- Run: `docker compose exec backend python manage.py collectstatic --noinput`
- Verify volume contents: `docker compose exec nginx ls /usr/src/app/static/`

### CORS errors in browser
- Check that `CORS_ALLOWED_ORIGINS` in `settings.py` includes `https://emailcampaign.musfiqdehan.com`
- Check that `CORS_ALLOW_CREDENTIALS = True`
