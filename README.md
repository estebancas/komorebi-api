# 🕯️ Komorebi API - E-commerce Candle Shop

A Flask-based REST API for a candle e-commerce shop, built with Python and Firebase Firestore.

## 🚀 Tech Stack

- **Backend**: Python 3.13 + Flask
- **API Documentation**: Flask-RESTX (Swagger/OpenAPI)
- **Database**: Firebase Firestore (NoSQL)
- **Authentication**: JWT tokens + bcrypt
- **Deployment**: Docker + Docker Compose
- **Production Server**: Gunicorn WSGI
- **Features**: Inventory Management, Order Processing, Payment Integration (SINPE)

## 🐳 Quick Start (Docker - Recommended)

The fastest way to get started is using Docker:

```bash
# 1. Copy environment template
cp .env.example .env

# 2. Edit .env with your Firebase credentials
nano .env  # or use your preferred editor

# 3. Start the application
docker-compose up --build

# 4. Access the API
# - API: http://localhost:8080
# - Health Check: http://localhost:8080/health
# - API Docs: http://localhost:8080/docs/
```

**For detailed Docker setup**, see [DOCKER_QUICKSTART.md](DOCKER_QUICKSTART.md)

**For deployment to cloud platforms**, see [DEPLOYMENT.md](DEPLOYMENT.md)

---

## 💻 Running Locally (Without Docker)

If you prefer to run without Docker:

## 📂 Project Structure

```
komorebi-api/
├── app/
│   ├── __init__.py              # Flask app factory
│   ├── models/
│   │   ├── user.py              # User model with roles
│   │   ├── product.py           # Product model with inventory
│   │   ├── category.py          # Category model
│   │   ├── cart.py              # Shopping cart
│   │   ├── order.py             # Order management
│   │   ├── inventory.py         # Inventory transactions (NEW)
│   │   ├── payment.py           # Payment processing
│   │   ├── address.py           # User addresses
│   │   └── role.py              # Role model
│   ├── routes/
│   │   ├── auth.py              # Authentication endpoints
│   │   ├── products.py          # Product CRUD
│   │   ├── categories.py        # Category management
│   │   ├── carts.py             # Shopping cart
│   │   ├── orders.py            # Order processing
│   │   ├── inventory.py         # Inventory management (NEW)
│   │   ├── addresses.py         # Address management
│   │   └── payment_methods.py   # Payment methods
│   ├── services/
│   │   ├── firebase_service.py  # Firebase/Firestore setup
│   │   └── jwt_service.py       # JWT token utilities
│   └── middleware/
│       └── auth.py              # JWT + role-based auth
├── scripts/
│   └── seed_roles.py            # Role seeding script
├── app.py                       # Dev entry point
├── run.py                       # Production entry point (NEW)
├── kmb.py                       # Management CLI
├── requirements.txt             # Python dependencies
├── Dockerfile                   # Production Docker image (NEW)
├── docker-compose.yml           # Local development setup (NEW)
├── .dockerignore                # Docker build exclusions (NEW)
├── .env.example                 # Environment template (NEW)
├── DEPLOYMENT.md                # Cloud deployment guide (NEW)
├── DOCKER_QUICKSTART.md         # Quick Docker setup (NEW)
└── TODO.md                      # Development roadmap
```

## Setup Instructions

### 1. Prerequisites

- Python 3.8 or higher
- Firebase project with Firestore enabled
- Firebase service account key

### 2. Clone and Setup Environment

```bash
# Clone the repository (if using git)
git clone <your-repo-url>
cd komorebi-api

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Firebase Configuration

1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Create a new project or select existing one
3. Enable Firestore Database
4. Generate a service account key:
   - Go to Project Settings → Service Accounts
   - Click "Generate new private key"
   - Download the JSON file

### 5. Environment Setup

Create a `.env` file from the template:

```bash
cp .env.example .env
```

Edit `.env` and add your Firebase credentials:

```bash
# Required configuration
FIREBASE_PROJECT_ID=your-project-id
FIREBASE_PRIVATE_KEY_ID=your-private-key-id
FIREBASE_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"
FIREBASE_CLIENT_EMAIL=your-service-account@your-project.iam.gserviceaccount.com
FIREBASE_CLIENT_ID=your-client-id
FIREBASE_AUTH_URI=https://accounts.google.com/o/oauth2/auth
FIREBASE_TOKEN_URI=https://oauth2.googleapis.com/token
JWT_SECRET_KEY=your-secret-key-here
```

**Generate a secure JWT secret:**

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 6. Run the Application

**Development Mode:**

```bash
python app.py
```

**Production Mode:**

```bash
gunicorn --bind 0.0.0.0:8080 --workers 4 run:app
```

## Management CLI

The project includes a management CLI (`kmb.py`) for administrative tasks like role management, data seeding, and more.

### Available Commands

**Get help:**

```bash
python kmb.py --help
```

**Role Management:**

Create a new role:

```bash
python kmb.py create-role --role "admin"
python kmb.py create-role --role "customer"
python kmb.py create-role -r "manager"  # Short form
```

List all existing roles:

```bash
python kmb.py list-roles
```

Get help for a specific command:

```bash
python kmb.py create-role --help
```

## 📚 API Documentation

Once the application is running, access the interactive API documentation:

- **Swagger UI**: http://localhost:8080/docs/
- **Health Check**: http://localhost:8080/health

### Key Features

- ✅ **User Authentication** - Register, login with JWT tokens
- ✅ **Product Management** - CRUD with pagination, search, sorting
- ✅ **Inventory System** - Stock tracking, transaction history, low-stock alerts
- ✅ **Shopping Cart** - Guest & authenticated user carts
- ✅ **Order Processing** - Complete checkout flow with status tracking
- ✅ **Payment Integration** - SINPE (Costa Rica), ready for Stripe/PayPal
- ✅ **Admin Dashboard** - Role-based access control for management
- ✅ **Categories** - Product categorization and filtering
- ✅ **Address Management** - Multiple shipping/billing addresses

---

## 🛠️ Development Tools

### Management CLI

Use the `kmb.py` CLI for administrative tasks:

```bash
# Get help
python kmb.py --help

# Create roles
python kmb.py create-role --role "admin"
python kmb.py create-role --role "customer"

# List all roles
python kmb.py list-roles
```

### Docker Commands

```bash
# Start in development mode (with hot reload)
docker-compose up

# View logs
docker-compose logs -f api

# Rebuild after dependency changes
docker-compose up --build

# Stop containers
docker-compose down

# Shell into container
docker-compose exec api bash
```

## 🔐 Security Notes

- ✅ `.env` file is gitignored (secrets not committed)
- ✅ JWT tokens for authentication
- ✅ Password hashing with bcrypt
- ✅ Role-based access control (RBAC)
- ✅ Non-root user in Docker container
- ✅ Environment variables for all secrets
- ⚠️ **Remember to change JWT_SECRET_KEY in production!**

---

## 🐛 Troubleshooting

### Docker Issues

**Container won't start:**

```bash
# Check logs
docker-compose logs api

# Verify .env file exists
ls -la .env

# Ensure port 8080 is free
lsof -i :8080
```

**Firebase connection errors:**

- Verify credentials in `.env` are correct
- Check Firebase project ID matches your Firebase console
- Ensure service account has Firestore permissions

**403 Forbidden on admin endpoints:**

- Add admin role to user in Firestore: `roles: ["admin"]`
- Check authentication debug logs

### Local Setup Issues

1. **Firebase Initialization Error**:

   - Check `.env` file has correct Firebase credentials
   - Verify all required environment variables are set

2. **Port Already in Use**:

   - Change port in `app.py` or `docker-compose.yml`
   - Or kill the process: `lsof -i :8080` then `kill <PID>`

3. **Import Errors**:

   - Ensure virtual environment is activated
   - Reinstall dependencies: `pip install -r requirements.txt`

4. **Authentication Issues**:
   - Verify JWT_SECRET_KEY is set in `.env`
   - Check token expiration
   - Ensure user exists in Firestore

---

## 📖 Additional Documentation

- [DOCKER_QUICKSTART.md](DOCKER_QUICKSTART.md) - Quick Docker setup guide
- [DEPLOYMENT.md](DEPLOYMENT.md) - Comprehensive deployment guide for cloud platforms
- [TODO.md](TODO.md) - Development roadmap and feature tracking
- [CLAUDE.md](CLAUDE.md) - Project context and development guidelines

---

_Built with ❤️ using Flask, Firebase, and Docker_
