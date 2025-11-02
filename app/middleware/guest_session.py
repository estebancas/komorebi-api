from functools import wraps
from flask import request, g
import uuid


def get_or_create_guest_session():
    """
    Get or create a guest session ID.
    Returns the session ID from cookie or creates a new one.
    """
    # Check if guest_session_id exists in cookie
    guest_session_id = request.cookies.get('guest_session_id')

    if not guest_session_id:
        # Generate new guest session ID
        guest_session_id = f"guest_{uuid.uuid4().hex}"

    return guest_session_id


def guest_session_handler(f):
    """
    Middleware to handle guest sessions.
    Sets g.guest_session_id and marks if cookie needs to be set.
    The actual cookie setting is done by after_request handler in app factory.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Get or create guest session
        guest_session_id = get_or_create_guest_session()
        g.guest_session_id = guest_session_id

        # Mark if we need to set the cookie
        if not request.cookies.get('guest_session_id'):
            g.set_guest_cookie = True
        else:
            g.set_guest_cookie = False

        # Call the route function and return directly
        # DON'T interfere with Flask-RESTX's response marshalling
        return f(*args, **kwargs)

    return decorated_function


def get_cart_identifier():
    """
    Get the cart identifier (user_id or guest_session_id).
    Should be called after jwt_required or optional_jwt middleware.
    Returns tuple: (identifier, is_authenticated)
    """
    # Check if user is authenticated
    if hasattr(g, 'current_user') and g.current_user:
        return (g.current_user.id, True)

    # Use guest session
    if hasattr(g, 'guest_session_id'):
        return (g.guest_session_id, False)

    # Fallback: create guest session
    guest_session_id = get_or_create_guest_session()
    g.guest_session_id = guest_session_id
    return (guest_session_id, False)
