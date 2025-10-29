from functools import wraps
from flask import request, jsonify, g
from app.services.jwt_service import verify_token
from app.models.user import User


def jwt_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = None
        auth_header = request.headers.get('Authorization')
        
        if auth_header:
            try:
                token = auth_header.split(' ')[1]
            except IndexError:
                return jsonify({'error': 'Invalid authorization header format'}), 401
        
        if not token:
            return jsonify({'error': 'Authorization token is required'}), 401
        
        user_id = verify_token(token)
        if not user_id:
            return jsonify({'error': 'Invalid or expired token'}), 401
        
        user = User.get_by_id(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 401
        
        g.current_user = user
        return f(*args, **kwargs)
    
    return decorated_function


def optional_jwt(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = None
        auth_header = request.headers.get('Authorization')
        
        if auth_header:
            try:
                token = auth_header.split(' ')[1]
                user_id = verify_token(token)
                if user_id:
                    user = User.get_by_id(user_id)
                    g.current_user = user
            except (IndexError, Exception):
                pass
        
        if not hasattr(g, 'current_user'):
            g.current_user = None
            
        return f(*args, **kwargs)
    
    return decorated_function