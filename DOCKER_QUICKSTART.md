# 🐳 Docker Quick Start Guide

Get your Komorebi API running in Docker in 5 minutes!

## ⚡ Quick Setup

### 1. Create your environment file
```bash
cp .env.example .env
```

### 2. Edit `.env` with your credentials
```bash
# Open in your editor
nano .env
# or
code .env
```

**Required values:**
- `FIREBASE_PROJECT_ID` - From Firebase Console
- `FIREBASE_PRIVATE_KEY` - From service account JSON
- `FIREBASE_CLIENT_EMAIL` - From service account JSON
- `JWT_SECRET_KEY` - Generate with: `python -c "import secrets; print(secrets.token_urlsafe(32))"`

### 3. Run with Docker Compose
```bash
# Build and start
docker-compose up --build

# Or run in background
docker-compose up -d
```

### 4. Test your API
```bash
# Health check
curl http://localhost:8082/health

# API docs
open http://localhost:8082/docs/
```

## 📝 Common Commands

```bash
# View logs
docker-compose logs -f

# Stop containers
docker-compose down

# Rebuild after code changes
docker-compose up --build

# Execute commands in container
docker-compose exec api python -m flask --version

# Shell into container
docker-compose exec api /bin/bash
```

## 🎯 Next Steps

- **Deploy to cloud**: See [DEPLOYMENT.md](DEPLOYMENT.md)
- **Configure admin user**: Add `roles: ["admin"]` to user in Firestore
- **Test endpoints**: Use Swagger UI at http://localhost:8082/docs/

## 🔐 Security Checklist

- [ ] `.env` file is NOT committed to git (check `.gitignore`)
- [ ] Changed `JWT_SECRET_KEY` from example value
- [ ] Using production Firebase project (not dev)
- [ ] Admin role properly configured in Firestore

## 🐛 Troubleshooting

**Container won't start?**
```bash
# Check logs
docker-compose logs api

# Verify .env file exists
ls -la .env

# Check port 8082 isn't in use
lsof -i :8082
```

**Firebase errors?**
- Verify credentials in `.env` are correct
- Check Firebase project ID matches
- Ensure service account has Firestore access

**403 on admin endpoints?**
- Add admin role to user in Firestore: `roles: ["admin"]`
- Check auth debug logs: `docker-compose logs -f api`

---

For detailed deployment instructions, see [DEPLOYMENT.md](DEPLOYMENT.md)
