from functools import wraps
from flask import request, g
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
                return {'error': 'Invalid authorization header format'}, 401

        if not token:
            return {'error': 'Authorization token is required'}, 401

        user_id = verify_token(token)

        if not user_id:
            return {'error': 'Invalid or expired token'}, 401

        user = User.get_by_id(user_id)
        if not user:
            return {'error': 'User not found'}, 401

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


def admin_required(f):
    """
    Decorator to require admin role for endpoint access.
    Must be used after @jwt_required decorator.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check if user is authenticated (should be set by @jwt_required)
        if not hasattr(g, 'current_user') or not g.current_user:
            return {'error': 'Authentication required'}, 401

        # Check if user has admin role
        has_admin = g.current_user.has_role_name('admin')

        if not has_admin:
            return {'error': 'Admin access required'}, 403

        return f(*args, **kwargs)

    return decorated_function