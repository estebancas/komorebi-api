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
    
    api.add_namespace(auth_ns)
    api.add_namespace(products_ns)
    api.add_namespace(users_ns)
    api.add_namespace(categories_ns)

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

    return app