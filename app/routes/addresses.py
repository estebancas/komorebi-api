from flask import request, g
from flask_restx import Namespace, Resource, fields
from app.models.address import Address
from app.middleware.auth import jwt_required

addresses_ns = Namespace('addresses', description='Address management operations', path='/addresses')

# Define models for request/response documentation
address_model = addresses_ns.model('Address', {
    'id': fields.String(description='Address ID'),
    'user_id': fields.String(description='User ID'),
    'address_type': fields.String(description='Address type (shipping, billing, both)',
                                   enum=['shipping', 'billing', 'both']),
    'recipient_name': fields.String(description='Recipient name'),
    'phone_number': fields.String(description='Phone number'),
    'street_address_1': fields.String(description='Street address line 1'),
    'street_address_2': fields.String(description='Street address line 2 (optional)'),
    'city': fields.String(description='City'),
    'state': fields.String(description='State/Province/Region'),
    'postal_code': fields.String(description='Postal/ZIP code'),
    'country': fields.String(description='Country'),
    'is_default': fields.Boolean(description='Whether this is the default address'),
    'created_at': fields.DateTime(description='Creation timestamp'),
    'updated_at': fields.DateTime(description='Last update timestamp')
})

address_create_model = addresses_ns.model('AddressCreate', {
    'address_type': fields.String(required=True, description='Address type (shipping, billing, both)',
                                   enum=['shipping', 'billing', 'both'], default='shipping'),
    'recipient_name': fields.String(required=True, description='Recipient name'),
    'phone_number': fields.String(required=True, description='Phone number'),
    'street_address_1': fields.String(required=True, description='Street address line 1'),
    'street_address_2': fields.String(required=False, description='Street address line 2 (optional)'),
    'city': fields.String(required=True, description='City'),
    'state': fields.String(required=True, description='State/Province/Region'),
    'postal_code': fields.String(required=True, description='Postal/ZIP code'),
    'country': fields.String(required=True, description='Country'),
    'is_default': fields.Boolean(required=False, description='Set as default address', default=False)
})

address_update_model = addresses_ns.model('AddressUpdate', {
    'address_type': fields.String(description='Address type (shipping, billing, both)',
                                   enum=['shipping', 'billing', 'both']),
    'recipient_name': fields.String(description='Recipient name'),
    'phone_number': fields.String(description='Phone number'),
    'street_address_1': fields.String(description='Street address line 1'),
    'street_address_2': fields.String(description='Street address line 2 (optional)'),
    'city': fields.String(description='City'),
    'state': fields.String(description='State/Province/Region'),
    'postal_code': fields.String(description='Postal/ZIP code'),
    'country': fields.String(description='Country'),
    'is_default': fields.Boolean(description='Set as default address')
})

addresses_list_model = addresses_ns.model('AddressesList', {
    'addresses': fields.List(fields.Nested(address_model), description='List of addresses'),
    'count': fields.Integer(description='Number of addresses')
})

validation_error_model = addresses_ns.model('ValidationError', {
    'errors': fields.List(fields.String, description='List of validation errors')
})


@addresses_ns.route('/')
class AddressList(Resource):
    @addresses_ns.doc('list_addresses',
                      description='Get all addresses for the authenticated user',
                      security='Bearer Auth')
    @addresses_ns.marshal_with(addresses_list_model)
    @jwt_required
    def get(self):
        """Get all addresses for the current user"""
        try:
            user_id = g.current_user.id
            addresses = Address.get_by_user_id(user_id)
            addresses_dict = [address.to_dict() for address in addresses]

            return {
                'addresses': addresses_dict,
                'count': len(addresses_dict)
            }, 200

        except Exception as e:
            addresses_ns.abort(500, f'Failed to retrieve addresses: {str(e)}')

    @addresses_ns.doc('create_address',
                      description='Create a new address for the authenticated user',
                      security='Bearer Auth')
    @addresses_ns.expect(address_create_model, validate=True)
    @addresses_ns.marshal_with(address_model, code=201)
    @addresses_ns.response(400, 'Validation Error', validation_error_model)
    @jwt_required
    def post(self):
        """Create a new address"""
        try:
            user_id = g.current_user.id
            data = request.json

            if not data:
                addresses_ns.abort(400, 'No data provided')

            # Create address
            address = Address(
                user_id=user_id,
                address_type=data.get('address_type', Address.TYPE_SHIPPING)
            )

            # Set address fields
            address.recipient_name = data.get('recipient_name', '').strip()
            address.phone_number = data.get('phone_number', '').strip()
            address.street_address_1 = data.get('street_address_1', '').strip()
            address.street_address_2 = data.get('street_address_2', '').strip()
            address.city = data.get('city', '').strip()
            address.state = data.get('state', '').strip()
            address.postal_code = data.get('postal_code', '').strip()
            address.country = data.get('country', '').strip()

            # Validate address
            validation_errors = address.validate()
            if validation_errors:
                return {'errors': validation_errors}, 400

            # Save address
            address.save()

            # Set as default if requested
            if data.get('is_default', False):
                address.set_as_default()

            return address.to_dict(), 201

        except Exception as e:
            addresses_ns.abort(500, f'Failed to create address: {str(e)}')


@addresses_ns.route('/<string:address_id>')
@addresses_ns.param('address_id', 'The address identifier')
class AddressItem(Resource):
    @addresses_ns.doc('get_address',
                      description='Get a specific address by ID',
                      security='Bearer Auth')
    @addresses_ns.marshal_with(address_model)
    @jwt_required
    def get(self, address_id):
        """Get an address by ID"""
        try:
            user_id = g.current_user.id
            address = Address.get_by_id(address_id)

            if not address:
                addresses_ns.abort(404, 'Address not found')

            # Ensure address belongs to current user
            if address.user_id != user_id:
                addresses_ns.abort(403, 'Access denied')

            return address.to_dict(), 200

        except Exception as e:
            addresses_ns.abort(500, f'Failed to retrieve address: {str(e)}')

    @addresses_ns.doc('update_address',
                      description='Update an existing address',
                      security='Bearer Auth')
    @addresses_ns.expect(address_update_model, validate=False)
    @addresses_ns.marshal_with(address_model)
    @addresses_ns.response(400, 'Validation Error', validation_error_model)
    @jwt_required
    def put(self, address_id):
        """Update an address"""
        try:
            user_id = g.current_user.id
            address = Address.get_by_id(address_id)

            if not address:
                addresses_ns.abort(404, 'Address not found')

            # Ensure address belongs to current user
            if address.user_id != user_id:
                addresses_ns.abort(403, 'Access denied')

            data = request.json
            if not data:
                addresses_ns.abort(400, 'No data provided')

            # Update fields if provided
            if 'address_type' in data:
                valid_types = [Address.TYPE_SHIPPING, Address.TYPE_BILLING, Address.TYPE_BOTH]
                if data['address_type'] not in valid_types:
                    addresses_ns.abort(400, f'Invalid address type. Must be one of: {", ".join(valid_types)}')
                address.address_type = data['address_type']

            if 'recipient_name' in data:
                address.recipient_name = data['recipient_name'].strip()

            if 'phone_number' in data:
                address.phone_number = data['phone_number'].strip()

            if 'street_address_1' in data:
                address.street_address_1 = data['street_address_1'].strip()

            if 'street_address_2' in data:
                address.street_address_2 = data['street_address_2'].strip()

            if 'city' in data:
                address.city = data['city'].strip()

            if 'state' in data:
                address.state = data['state'].strip()

            if 'postal_code' in data:
                address.postal_code = data['postal_code'].strip()

            if 'country' in data:
                address.country = data['country'].strip()

            # Validate updated address
            validation_errors = address.validate()
            if validation_errors:
                return {'errors': validation_errors}, 400

            # Save updated address
            address.save()

            # Handle default flag
            if 'is_default' in data and data['is_default']:
                address.set_as_default()
            elif 'is_default' in data and not data['is_default']:
                # If explicitly setting to False, just save (don't unset other defaults)
                address.is_default = False
                address.save()

            return address.to_dict(), 200

        except Exception as e:
            addresses_ns.abort(500, f'Failed to update address: {str(e)}')

    @addresses_ns.doc('delete_address',
                      description='Delete an address',
                      security='Bearer Auth')
    @jwt_required
    def delete(self, address_id):
        """Delete an address"""
        try:
            user_id = g.current_user.id
            address = Address.get_by_id(address_id)

            if not address:
                addresses_ns.abort(404, 'Address not found')

            # Ensure address belongs to current user
            if address.user_id != user_id:
                addresses_ns.abort(403, 'Access denied')

            if address.delete():
                return {'message': 'Address deleted successfully'}, 200
            else:
                addresses_ns.abort(500, 'Failed to delete address')

        except Exception as e:
            addresses_ns.abort(500, f'Failed to delete address: {str(e)}')


@addresses_ns.route('/default')
class DefaultAddress(Resource):
    @addresses_ns.doc('get_default_address',
                      description='Get the default address for the authenticated user',
                      security='Bearer Auth')
    @addresses_ns.marshal_with(address_model)
    @addresses_ns.param('type', 'Address type filter (shipping, billing)', type=str, required=False)
    @jwt_required
    def get(self):
        """Get the default address, optionally filtered by type"""
        try:
            user_id = g.current_user.id
            address_type = request.args.get('type', '').strip()

            # Validate type if provided
            if address_type:
                valid_types = [Address.TYPE_SHIPPING, Address.TYPE_BILLING]
                if address_type not in valid_types:
                    addresses_ns.abort(400, f'Invalid address type. Must be one of: {", ".join(valid_types)}')

            address = Address.get_default_by_user_id(
                user_id,
                address_type=address_type if address_type else None
            )

            if not address:
                addresses_ns.abort(404, 'No default address found')

            return address.to_dict(), 200

        except Exception as e:
            addresses_ns.abort(500, f'Failed to retrieve default address: {str(e)}')


@addresses_ns.route('/<string:address_id>/set-default')
@addresses_ns.param('address_id', 'The address identifier')
class SetDefaultAddress(Resource):
    @addresses_ns.doc('set_default_address',
                      description='Set an address as the default for the user',
                      security='Bearer Auth')
    @addresses_ns.marshal_with(address_model)
    @jwt_required
    def put(self, address_id):
        """Set an address as default"""
        try:
            user_id = g.current_user.id
            address = Address.get_by_id(address_id)

            if not address:
                addresses_ns.abort(404, 'Address not found')

            # Ensure address belongs to current user
            if address.user_id != user_id:
                addresses_ns.abort(403, 'Access denied')

            # Set as default
            address.set_as_default()

            return address.to_dict(), 200

        except Exception as e:
            addresses_ns.abort(500, f'Failed to set default address: {str(e)}')
