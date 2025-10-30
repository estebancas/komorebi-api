from flask import Flask, jsonify, g
from flask_restx import Api, Resource
from app.services.firebase_service import initialize_firebase
from app.middleware.auth import jwt_required


def create_app():
    app = Flask(__name__)
    
    # Configure Flask-RESTX
    api = Api(
        app,
        version='1.0',
        title='Komorebi Candle Shop API',
        description='A REST API for an e-commerce candle shop',
        doc='/docs/',  # Swagger UI endpoint
        prefix='/api'
    )

    initialize_firebase()

    # Import and register namespaces
    from app.routes.auth import auth_ns
    from app.routes.products import products_ns
    from app.routes.users import users_ns
    from app.routes.categories import categories_ns
    from app.routes.carts import carts_ns
    from app.routes.orders import orders_ns

    api.add_namespace(auth_ns)
    api.add_namespace(products_ns)
    api.add_namespace(users_ns)
    api.add_namespace(categories_ns)
    api.add_namespace(carts_ns)
    api.add_namespace(orders_ns)

    @app.route('/health')
    def health_check():
        return {'status': 'healthy'}, 200

    @app.route('/protected')
    @jwt_required
    def protected_route():
        return jsonify({
            'message': 'This is a protected route',
            'user': g.current_user.to_dict()
        }), 200

    # After request handler to set guest session cookie
    @app.after_request
    def set_guest_session_cookie(response):
        """Set guest session cookie if needed after response is ready"""
        if hasattr(g, 'set_guest_cookie') and g.set_guest_cookie:
            if hasattr(g, 'guest_session_id'):
                print(f"[DEBUG] after_request: Setting guest cookie: {g.guest_session_id}")
                response.set_cookie(
                    'guest_session_id',
                    g.guest_session_id,
                    max_age=30*24*60*60,  # 30 days
                    httponly=True,
                    samesite='Lax'
                )
        return response

    return app