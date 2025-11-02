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
    'role_ids': fields.List(fields.String, description='List of role IDs'),
    'roles': fields.List(fields.String, description='List of role names (if included)', required=False),
    'created_at': fields.String(description='Creation timestamp'),
    'updated_at': fields.String(description='Last update timestamp')
})

users_list_model = users_ns.model('UsersList', {
    'users': fields.List(fields.Nested(user_model), description='List of users'),
    'count': fields.Integer(description='Number of users')
})


@users_ns.route('/')
class UserList(Resource):
    @users_ns.doc('list_users')
    @users_ns.marshal_with(users_list_model)
    @users_ns.param('include_roles', 'Include user roles in response', type=bool, default=False)
    def get(self):
        """Get all users"""
        try:
            include_roles = request.args.get('include_roles', 'false').lower() == 'true'
            users = User.get_all()
            users_dict = [user.to_dict(include_roles=include_roles) for user in users]

            return {
                'users': users_dict,
                'count': len(users_dict)
            }, 200

        except Exception:
            users_ns.abort(500, 'Failed to retrieve users')

