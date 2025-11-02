# 🚀 Komorebi API - Deployment Guide

This guide covers deploying the Komorebi Candle Shop API using Docker and various cloud platforms.

## 📋 Prerequisites

- Docker and Docker Compose installed
- Firebase project with Firestore enabled
- Firebase service account credentials

---

## 🐳 Docker Deployment

### Local Development with Docker Compose

1. **Create your environment file:**
   ```bash
   cp .env.example .env
   ```

2. **Edit `.env` with your actual credentials:**
   - Get Firebase credentials from Firebase Console → Project Settings → Service Accounts
   - Generate a strong JWT secret key:
     ```bash
     python -c "import secrets; print(secrets.token_urlsafe(32))"
     ```

3. **Build and run:**
   ```bash
   # Build and start containers
   docker-compose up --build

   # Run in detached mode (background)
   docker-compose up -d

   # View logs
   docker-compose logs -f

   # Stop containers
   docker-compose down
   ```

4. **Access the API:**
   - API: http://localhost:8080
   - Health check: http://localhost:8080/health
   - API docs: http://localhost:8080/docs/

### Production Docker Build

```bash
# Build the image
docker build -t komorebi-api:latest .

# Run the container
docker run -d \
  --name komorebi-api \
  -p 8080:8080 \
  --env-file .env \
  komorebi-api:latest

# Check logs
docker logs -f komorebi-api

# Stop container
docker stop komorebi-api
```

---

## ☁️ Cloud Platform Deployment

### Option 1: Google Cloud Run (Recommended)

**Why Cloud Run?**
- You're already using Firebase/Firestore (same ecosystem)
- Generous free tier (2M requests/month)
- Auto-scales to zero (no cost when idle)
- Easiest integration with Firebase

**Prerequisites:**
- Google Cloud account
- gcloud CLI installed

**Deployment Steps:**

1. **Install gcloud CLI:**
   ```bash
   # macOS
   brew install google-cloud-sdk

   # Or download from: https://cloud.google.com/sdk/docs/install
   ```

2. **Authenticate and set project:**
   ```bash
   gcloud auth login
   gcloud config set project YOUR_FIREBASE_PROJECT_ID
   ```

3. **Deploy to Cloud Run:**
   ```bash
   # Deploy directly from source
   gcloud run deploy komorebi-api \
     --source . \
     --region us-central1 \
     --allow-unauthenticated \
     --set-env-vars FIREBASE_PROJECT_ID=YOUR_PROJECT_ID \
     --set-env-vars JWT_SECRET_KEY=YOUR_JWT_SECRET \
     --platform managed
   ```

4. **Set Firebase credentials as secrets (recommended):**
   ```bash
   # Create secret for Firebase private key
   echo "YOUR_PRIVATE_KEY" | gcloud secrets create firebase-private-key --data-file=-

   # Deploy with secret
   gcloud run deploy komorebi-api \
     --source . \
     --region us-central1 \
     --allow-unauthenticated \
     --update-secrets=FIREBASE_PRIVATE_KEY=firebase-private-key:latest
   ```

5. **Your API is now live!**
   - Cloud Run will provide a URL like: https://komorebi-api-xxxxx-uc.a.run.app
   - Access docs at: https://YOUR-URL/docs/

**Cost Estimate:**
- Free tier: 2M requests, 360,000 GB-seconds/month
- After free tier: ~$0.40 per million requests
- Typical small shop: **$0-5/month**

---

### Option 2: Render

**Why Render?**
- Simple setup (connects to GitHub)
- Free tier available
- Auto-deploys on git push

**Deployment Steps:**

1. **Push code to GitHub** (if not already done)

2. **Create Render account:** https://render.com

3. **Create new Web Service:**
   - Connect your GitHub repository
   - Select "Docker" as environment
   - Set Docker command: (auto-detected from Dockerfile)

4. **Add environment variables in Render dashboard:**
   ```
   FIREBASE_PROJECT_ID=your-project-id
   FIREBASE_PRIVATE_KEY_ID=your-key-id
   FIREBASE_PRIVATE_KEY=your-private-key
   FIREBASE_CLIENT_EMAIL=your-email
   FIREBASE_CLIENT_ID=your-client-id
   FIREBASE_AUTH_URI=https://accounts.google.com/o/oauth2/auth
   FIREBASE_TOKEN_URI=https://oauth2.googleapis.com/token
   JWT_SECRET_KEY=your-jwt-secret
   ```

5. **Deploy!**
   - Render will automatically build and deploy
   - Access your API at: https://your-app-name.onrender.com

**Important Notes:**
- Free tier spins down after 15 mins of inactivity (cold starts)
- Upgrade to paid tier ($7/month) for always-on service

**Cost Estimate:**
- Free tier available (with cold starts)
- Paid: $7/month for hobby tier

---

### Option 3: Railway

**Why Railway?**
- $5 free credits/month
- Better performance than Render
- Good developer experience

**Deployment Steps:**

1. **Create Railway account:** https://railway.app

2. **Install Railway CLI:**
   ```bash
   npm i -g @railway/cli
   # or
   brew install railway
   ```

3. **Login and deploy:**
   ```bash
   railway login
   railway init
   railway up
   ```

4. **Add environment variables:**
   ```bash
   # Via CLI
   railway variables set FIREBASE_PROJECT_ID=your-project-id
   railway variables set JWT_SECRET_KEY=your-secret

   # Or via Railway dashboard
   ```

5. **Your app is deployed!**
   - Access at your Railway-provided URL
   - Can add custom domain

**Cost Estimate:**
- $5 free credits/month
- After that: usage-based (~$5-10/month for small apps)

---

### Option 4: Fly.io

**Why Fly.io?**
- Edge deployment (fast globally)
- Free tier includes 3 VMs
- Docker-native

**Deployment Steps:**

1. **Install flyctl:**
   ```bash
   brew install flyctl
   ```

2. **Login and launch:**
   ```bash
   fly auth login
   fly launch
   ```

3. **Set secrets:**
   ```bash
   fly secrets set JWT_SECRET_KEY=your-secret
   fly secrets set FIREBASE_PROJECT_ID=your-project-id
   # ... add all other env vars
   ```

4. **Deploy:**
   ```bash
   fly deploy
   ```

**Cost Estimate:**
- Free tier: 3 shared VMs, 160GB bandwidth
- Typical usage: $0-5/month

---

## 🔐 Managing Secrets in Production

### Never commit secrets to git!

**Methods for managing secrets:**

1. **Environment Variables (most platforms):**
   - Set in platform dashboard
   - Injected at runtime

2. **Google Cloud Secret Manager (for GCP):**
   ```bash
   # Create secret
   gcloud secrets create my-secret --data-file=secret.txt

   # Grant access to Cloud Run
   gcloud secrets add-iam-policy-binding my-secret \
     --member=serviceAccount:YOUR-SERVICE-ACCOUNT \
     --role=roles/secretmanager.secretAccessor
   ```

3. **Docker Secrets (for Docker Swarm):**
   ```bash
   echo "my-secret" | docker secret create jwt_secret -
   ```

---

## 🧪 Testing Your Deployment

### Health Check
```bash
curl https://your-api-url/health
```

Expected response:
```json
{
  "status": "healthy"
}
```

### API Documentation
Visit: `https://your-api-url/docs/`

### Test Authentication
```bash
# Register a user
curl -X POST https://your-api-url/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"Test123!","name":"Test User"}'

# Login
curl -X POST https://your-api-url/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"Test123!"}'
```

---

## 📊 Monitoring & Logs

### Docker Compose
```bash
docker-compose logs -f
```

### Cloud Run
```bash
gcloud run logs tail komorebi-api
```

### Render
- View logs in Render dashboard
- Real-time log streaming available

### Railway
```bash
railway logs
```

---

## 🔄 CI/CD Setup (Optional)

### GitHub Actions for Cloud Run

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy to Cloud Run

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Google Auth
        uses: google-github-actions/auth@v1
        with:
          credentials_json: ${{ secrets.GCP_SA_KEY }}

      - name: Deploy to Cloud Run
        run: |
          gcloud run deploy komorebi-api \
            --source . \
            --region us-central1 \
            --allow-unauthenticated
```

---

## 🆘 Troubleshooting

### Container won't start
```bash
# Check logs
docker logs komorebi-api

# Common issues:
# - Missing environment variables
# - Invalid Firebase credentials
# - Port already in use
```

### Health check failing
```bash
# Test locally
curl http://localhost:8080/health

# Check if app is binding to correct port (8080)
```

### Firebase connection errors
```bash
# Verify credentials are set
docker exec komorebi-api env | grep FIREBASE

# Check Firebase project ID matches
# Ensure service account has Firestore access
```

### 403 Forbidden on admin endpoints
- Make sure user has 'admin' role in Firestore
- See debug logs from auth middleware
- Verify JWT token is valid

---

## 📈 Scaling Considerations

### For growing traffic:

1. **Vertical Scaling:**
   - Increase workers in gunicorn:
     ```bash
     gunicorn --workers 8 --threads 4 run:app
     ```

2. **Horizontal Scaling:**
   - Cloud Run auto-scales (no config needed)
   - Docker Swarm/Kubernetes for self-hosted

3. **Database Optimization:**
   - Firestore automatically scales
   - Consider caching frequently accessed data

4. **CDN for Static Assets:**
   - Cloud CDN (if using Cloud Run)
   - Cloudflare (works with any platform)

---

## 💰 Cost Comparison Summary

| Platform | Free Tier | Paid Tier | Best For |
|----------|-----------|-----------|----------|
| **Google Cloud Run** | 2M requests/mo | Pay-per-use (~$5-20/mo) | Production, already using Firebase |
| **Render** | Yes (with cold starts) | $7/mo (always-on) | Simple setup, learning |
| **Railway** | $5 credits/mo | Usage-based (~$5-10/mo) | Good balance of features/cost |
| **Fly.io** | 3 VMs free | Usage-based (~$5-10/mo) | Global edge deployment |
| **AWS/Heroku** | Limited/None | $25+/mo | Enterprise, complex needs |

**Recommendation for Komorebi:**
- **Development:** Docker Compose (local)
- **Production:** Google Cloud Run (best integration with Firebase)
- **Budget Alternative:** Render free tier → Railway when scaling

---

## 📞 Support

For deployment issues:
- Check [TODO.md](TODO.md) for current status
- Review API docs at `/docs/`
- Check platform-specific documentation

---

_Last updated: 01/11/25_
