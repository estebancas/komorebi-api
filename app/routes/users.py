from flask import request
from flask_restx import Namespace, Resource, fields
from app.models.user import User

users_ns = Namespace('users', description='User operations', path='/users')

# Define models for request/response documentation
user_model = users_ns.model('User', {
    'id': fields.String(description='User ID'),
    'email': fields.String(description='User email'),
    'first_name': fields.String(description='First name'),
    'last_name': fields.String(description='Last name'),
    'role': fields.String(description='User role'),
    'created_at': fields.DateTime(description='Creation timestamp'),
    'updated_at': fields.DateTime(description='Last update timestamp')
})

users_list_model = users_ns.model('UsersList', {
    'users': fields.List(fields.Nested(user_model), description='List of users'),
    'count': fields.Integer(description='Number of users')
})


@users_ns.route('/')
class UserList(Resource):
    @users_ns.doc('list_users')
    @users_ns.marshal_with(users_list_model)
    def get(self):
        """Get all users"""
        try:
            users = User.get_all(True)
            users_dict = [user.to_dict() for user in users]

            return {
                'users': users_dict,
                'count': len(users_dict)
            }, 200
            
        except Exception:
            users_ns.abort(500, 'Failed to retrieve users')

