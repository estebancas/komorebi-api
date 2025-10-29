# Komorebi API - E-commerce Candle Shop

A Flask-based REST API for a candle e-commerce shop, built with Python and Firebase Firestore.

## Tech Stack

- **Backend**: Python 3.x + Flask
- **API Documentation**: Flask-RESTX (Swagger/OpenAPI)
- **Database**: Firebase Firestore
- **Authentication**: JWT tokens
- **Password Hashing**: bcrypt

## Project Structure

```
komorebi-api/
├── app/
│   ├── __init__.py           # Flask app factory
│   ├── models/
│   │   ├── user.py          # User model with roles
│   │   ├── product.py       # Product model
│   │   └── role.py          # Role model
│   ├── routes/
│   │   ├── auth.py          # Authentication endpoints
│   │   └── products.py      # Product endpoints
│   ├── services/
│   │   ├── firebase_service.py  # Firebase initialization
│   │   └── jwt_service.py       # JWT utilities
│   └── middleware/
│       └── auth.py              # JWT middleware
├── app.py                       # Application entry point
├── requirements.txt             # Python dependencies
└── serviceAccountKey.json       # Firebase credentials
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
   - Save the JSON file as `serviceAccountKey.json` in the root directory

### 5. Environment Setup (Optional)

Create a `.env` file for environment variables (if needed):

```bash
# .env
FLASK_ENV=development
FLASK_DEBUG=True
```

## Running the Application

### Development Mode

```bash
# Make sure virtual environment is activated
python app.py
```

The API will be available at `http://localhost:5000`

### API Documentation

The interactive API documentation (Swagger UI) is available at:
- **Documentation URL**: `http://localhost:5000/docs/`
- **Features**:
  - Interactive interface to test all endpoints
  - Request/response schemas with validation
  - Authentication support for protected endpoints
  - Detailed parameter descriptions and examples

### Production Mode

```bash
# Using Gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

## API Endpoints

> 📋 **Interactive Documentation**: Visit `http://localhost:5000/docs/` for the complete interactive API documentation with try-it-out functionality!

All API endpoints are now prefixed with `/api` and fully documented with Flask-RESTX.

### Health Check
- `GET /health` - Check if the API is running

### Authentication (`/api/auth`)
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login user

### Products (`/api/products`)
- `GET /api/products/` - Get all products (with pagination, search, sorting)
  - Query parameters: `page`, `per_page`, `search`, `sort_by`, `sort_order`
- `POST /api/products/` - Create new product
- `GET /api/products/<id>` - Get specific product
- `PUT /api/products/<id>` - Update product (partial updates supported)
- `DELETE /api/products/<id>` - Delete product

### Users (`/api/users`)
- `GET /api/users/` - Get all users

### Protected Routes
- `GET /protected` - Test protected route (requires auth)

## Models

### User
- Fields: `id`, `email`, `first_name`, `last_name`, `role_ids`, `created_at`, `updated_at`
- Supports multiple roles per user
- Password hashing with bcrypt

### Role
- Fields: `id`, `name`, `created_at`, `updated_at`
- Used for user permissions and access control

### Product
- Fields: `id`, `name`, `description`, `media`, `price`, `category`, `stock`, etc.
- Full e-commerce product management

## Testing the API

### Option 1: Interactive Documentation (Recommended)

Visit `http://localhost:5000/docs/` for the interactive Swagger UI where you can:
- Test all endpoints directly in the browser
- See request/response schemas
- Get example payloads
- Handle authentication automatically

### Option 2: Using curl

```bash
# Health check
curl http://localhost:5000/health

# Register user
curl -X POST http://localhost:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "password123", "first_name": "Test", "last_name": "User"}'

# Login
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "password123"}'

# Get products with search and pagination
curl "http://localhost:5000/api/products/?page=1&per_page=10&search=vanilla&sort_by=created_at&sort_order=desc"
```

### Option 3: Postman/Insomnia

You can import the OpenAPI specification from `http://localhost:5000/swagger.json` for automatic endpoint setup.

## Development Notes

- The project uses Flask's application factory pattern
- JWT tokens are used for authentication
- Firestore is used as the primary database
- User passwords are hashed using bcrypt
- Role-based access control is implemented

## Troubleshooting

### Common Issues

1. **Firebase Initialization Error**: Ensure `serviceAccountKey.json` is in the root directory
2. **Port Already in Use**: Change the port in `app.py` or kill the process using the port
3. **Import Errors**: Make sure virtual environment is activated and dependencies are installed

### Logs

Check the console output for detailed error messages and debugging information.