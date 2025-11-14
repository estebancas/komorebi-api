# CLAUDE.md - E-commerce Project (komorebi-api)

## Context

This repository is for building a small e-commerce REST API for a candle shop.
The project serves a **dual purpose**:

1. A **learning environment** where I improve my Python and Flask skills.
2. A **production-ready application** that I plan to eventually deploy and use.

## Expectations for the Agent

- Act as a **Python and Flask mentor**, guiding me through best practices while still explaining concepts clearly.
- Balance between **teaching mode** (when I ask about fundamentals) and **developer mode** (when I need direct solutions).
- When possible, explain trade-offs between "learning-oriented" approaches and "production-ready" implementations.
- Correct my code with explanations of _why_ something is wrong and _how_ to improve it.
- Suggest improvements that make the code more robust for real-world usage.
- Assume I already know **Docker**, so avoid unnecessary container basics.

## Scope

- Core tech: **Python + Flask** for the REST API, **Firestore** (Firebase) for database.
- Example domain: candle e-commerce (products, orders, users, inventory).
- Infrastructure: use Docker for packaging, but keep explanations focused on Python and Flask.
- CI/CD, testing, and deployment can be introduced progressively, but not the main focus at the start.

## Teaching Style

- Provide clear, progressive explanations when introducing new Python or Flask concepts.
- Reinforce key ideas with small, practical examples tied to the e-commerce context.
- Encourage me to write code myself instead of just copying solutions.
- When explaining advanced or production topics, break them down into approachable steps.

## Tech Stack

- python
- flask
- flask-restx (for API documentation and validation)
- firestore
- boto3 (AWS SDK for S3 file storage)

## Cloud Storage Configuration

### AWS S3 Setup

The application uses AWS S3 for secure image storage with a security-first approach. The backend server has full control over file operations, while direct client access to S3 is completely blocked.

#### IAM User Configuration

- **Access Type**: Programmatic access only (no AWS Console access)
- **Purpose**: Dedicated service account for the Python backend to interact with S3
- **Credentials**: Stored as environment variables, never committed to version control

#### IAM Policy (Minimalist Permissions)

A custom IAM policy is attached to the user with the least privileges necessary:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:PutObject",
        "s3:GetObject",
        "s3:DeleteObject"
      ],
      "Resource": "arn:aws:s3:::<my-bucket-name>/*"
    }
  ]
}
```

**Key Points**:
- Only three operations allowed: upload, read, and delete
- No bucket-level permissions (cannot list, create, or delete buckets)
- Scoped to a specific bucket using ARN
- Cannot modify bucket settings or permissions

#### S3 Bucket Security

- **Block Public Access**: All four Block Public Access settings are enabled at the bucket level
  - Block public access to buckets and objects granted through new ACLs
  - Block public access to buckets and objects granted through any ACLs
  - Block public access to buckets and objects granted through new public bucket or access point policies
  - Block public and cross-account access to buckets and objects through any public bucket or access point policies
- **Object-level ACLs**: Individual objects can be marked as `public-read` when uploaded (via `boto3.upload_fileobj()`)
- **Result**: The bucket itself is private, but specific images can be made publicly accessible via their URLs

#### Backend Implementation

**Environment Variables** (configured in `.env`):
```bash
AWS_ACCESS_KEY_ID=<IAM_user_access_key>
AWS_SECRET_ACCESS_KEY=<IAM_user_secret_key>
AWS_S3_BUCKET_NAME=<bucket_name>
AWS_REGION=<region>  # e.g., us-east-1
```

**File Upload Flow**:
1. Frontend (Next.js) sends image file to Python backend endpoint
2. Backend validates file type and size
3. Backend generates secure, unique filename (UUID-based)
4. Backend uploads to S3 using `boto3.upload_fileobj()`
5. Backend returns public URL to frontend
6. Backend stores image URL in Firestore database

**Security Benefits**:
- Frontend **never** has direct S3 credentials or access
- All file validation happens server-side
- Prevents malicious uploads or unauthorized deletions
- Centralized control over file naming and organization
- Easy to audit and log all file operations

**Code Reference**: See [app/services/s3_service.py](app/services/s3_service.py) for the complete implementation.

## API Development Standards

**IMPORTANT**: ALL new API endpoints must be built using Flask-RESTX patterns:

- Use `Namespace` instead of `Blueprint`
- Use `Resource` classes instead of route functions
- Define proper request/response models with `fields` for documentation
- Include `@doc` decorators for endpoint descriptions
- Use `@marshal_with` for response serialization and `@expect` for request validation
- Follow the existing pattern established in `/routes/products.py`, `/routes/auth.py`, and `/routes/users.py`
- Ensure all endpoints are automatically documented in the Swagger UI at `/docs/`
- Use `namespace.abort()` for error handling instead of `jsonify()` with error codes

**Example pattern to follow**:
```python
@products_ns.route('/')
class ProductList(Resource):
    @products_ns.doc('list_products')
    @products_ns.marshal_with(products_list_model)
    def get(self):
        """Get all products"""
        # implementation
```
