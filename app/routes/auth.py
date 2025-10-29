from flask import request
from flask_restx import Namespace, Resource, fields
from app.models.user import User
from app.services.jwt_service import generate_token

auth_ns = Namespace('auth', description='Authentication operations', path='/auth')

# Define models for request/response documentation
user_model = auth_ns.model('User', {
    'id': fields.String(description='User ID'),
    'email': fields.String(description='User email'),
    'first_name': fields.String(description='First name'),
    'last_name': fields.String(description='Last name'),
    'role': fields.String(description='User role'),
    'created_at': fields.DateTime(description='Creation timestamp'),
    'updated_at': fields.DateTime(description='Last update timestamp')
})

register_model = auth_ns.model('RegisterRequest', {
    'email': fields.String(required=True, description='User email'),
    'password': fields.String(required=True, description='User password'),
    'first_name': fields.String(description='First name'),
    'last_name': fields.String(description='Last name')
})

login_model = auth_ns.model('LoginRequest', {
    'email': fields.String(required=True, description='User email'),
    'password': fields.String(required=True, description='User password')
})

auth_response_model = auth_ns.model('AuthResponse', {
    'message': fields.String(description='Response message'),
    'token': fields.String(description='JWT token'),
    'user': fields.Nested(user_model, description='User information')
})


@auth_ns.route('/register')
class Register(Resource):
    @auth_ns.doc('register_user')
    @auth_ns.expect(register_model, validate=True)
    @auth_ns.marshal_with(auth_response_model, code=201)
    def post(self):
        """Register a new user"""
        data = request.json
        
        if not data:
            auth_ns.abort(400, 'No data provided')
        
        email = data.get('email', '').strip()
        password = data.get('password', '')
        first_name = data.get('first_name', '').strip()
        last_name = data.get('last_name', '').strip()
        
        if not email or not password:
            auth_ns.abort(400, 'Email and password are required')
        
        if not User.validate_email(email):
            auth_ns.abort(400, 'Invalid email format')
        
        if len(password) < 6:
            auth_ns.abort(400, 'Password must be at least 6 characters')
        
        existing_user = User.get_by_email(email)
        if existing_user:
            auth_ns.abort(400, 'Email already registered')
        
        try:
            user = User(email=email, password=password, first_name=first_name, last_name=last_name)
            user.save()
            
            token = generate_token(user.id, email)
            
            return {
                'message': 'User registered successfully',
                'token': token,
                'user': user.to_dict()
            }, 201
            
        except Exception:
            auth_ns.abort(500, 'Registration failed')


@auth_ns.route('/login')
class Login(Resource):
    @auth_ns.doc('login_user')
    @auth_ns.expect(login_model, validate=True)
    @auth_ns.marshal_with(auth_response_model)
    def post(self):
        """Login a user"""
        data = request.json
        
        if not data:
            auth_ns.abort(400, 'No data provided')
        
        email = data.get('email', '').strip()
        password = data.get('password', '')
        
        if not email or not password:
            auth_ns.abort(400, 'Email and password are required')
        
        user = User.get_by_email(email)
        if not user or not user.check_password(password):
            auth_ns.abort(401, 'Invalid email or password')
        
        try:
            token = generate_token(user.id, user.email)
            
            return {
                'message': 'Login successful',
                'token': token,
                'user': user.to_dict()
            }, 200
            
        except Exception:
            auth_ns.abort(500, 'Login failed')