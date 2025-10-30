from flask import request, g
from flask_restx import Namespace, Resource, fields
from app.models.payment_method import PaymentMethod
from app.middleware.auth import jwt_required

payment_methods_ns = Namespace('payment-methods', description='Payment method management operations',
                                path='/payment-methods')

# Define models for request/response documentation
payment_method_model = payment_methods_ns.model('PaymentMethod', {
    'id': fields.String(description='Payment method ID'),
    'user_id': fields.String(description='User ID'),
    'method_type': fields.String(description='Payment method type',
                                  enum=['credit_card', 'debit_card', 'paypal', 'bank_account', 'other']),
    'gateway': fields.String(description='Payment gateway',
                             enum=['stripe', 'paypal', 'manual']),
    'card_last_four': fields.String(description='Last 4 digits of card'),
    'card_brand': fields.String(description='Card brand (visa, mastercard, amex, etc.)'),
    'card_exp_month': fields.Integer(description='Card expiration month (1-12)'),
    'card_exp_year': fields.Integer(description='Card expiration year'),
    'card_funding': fields.String(description='Card funding type (credit, debit, prepaid)'),
    'paypal_email': fields.String(description='PayPal email address'),
    'bank_name': fields.String(description='Bank name'),
    'bank_last_four': fields.String(description='Last 4 digits of bank account'),
    'bank_account_type': fields.String(description='Bank account type (checking, savings)'),
    'billing_address_id': fields.String(description='Billing address ID'),
    'cardholder_name': fields.String(description='Cardholder name'),
    'nickname': fields.String(description='User-friendly nickname for the payment method'),
    'is_default': fields.Boolean(description='Whether this is the default payment method'),
    'is_active': fields.Boolean(description='Whether this payment method is active'),
    'is_expired': fields.Boolean(description='Whether this card is expired'),
    'display_name': fields.String(description='User-friendly display name'),
    'masked_number': fields.String(description='Masked card/account number'),
    'expiration': fields.String(description='Formatted expiration date (MM/YY)'),
    'created_at': fields.DateTime(description='Creation timestamp'),
    'updated_at': fields.DateTime(description='Last update timestamp'),
    'last_used_at': fields.DateTime(description='Last used timestamp')
})

payment_method_create_model = payment_methods_ns.model('PaymentMethodCreate', {
    'method_type': fields.String(required=True, description='Payment method type',
                                  enum=['credit_card', 'debit_card', 'paypal', 'bank_account', 'other'],
                                  default='credit_card'),
    'gateway': fields.String(required=True, description='Payment gateway',
                             enum=['stripe', 'paypal', 'manual'], default='stripe'),
    'gateway_customer_id': fields.String(description='Gateway customer ID (e.g., Stripe customer ID)'),
    'gateway_payment_method_id': fields.String(description='Gateway payment method ID'),
    'card_last_four': fields.String(description='Last 4 digits of card (required for card types)'),
    'card_brand': fields.String(description='Card brand (required for card types)'),
    'card_exp_month': fields.Integer(description='Card expiration month (1-12)'),
    'card_exp_year': fields.Integer(description='Card expiration year'),
    'card_funding': fields.String(description='Card funding type (credit, debit, prepaid)'),
    'paypal_email': fields.String(description='PayPal email address (required for PayPal)'),
    'bank_name': fields.String(description='Bank name'),
    'bank_last_four': fields.String(description='Last 4 digits of bank account'),
    'bank_account_type': fields.String(description='Bank account type (checking, savings)'),
    'billing_address_id': fields.String(description='Billing address ID'),
    'cardholder_name': fields.String(description='Cardholder name'),
    'nickname': fields.String(description='User-friendly nickname'),
    'is_default': fields.Boolean(description='Set as default payment method', default=False)
})

payment_method_update_model = payment_methods_ns.model('PaymentMethodUpdate', {
    'nickname': fields.String(description='User-friendly nickname'),
    'billing_address_id': fields.String(description='Billing address ID'),
    'cardholder_name': fields.String(description='Cardholder name'),
    'is_default': fields.Boolean(description='Set as default payment method'),
    'is_active': fields.Boolean(description='Set as active or inactive')
})

payment_methods_list_model = payment_methods_ns.model('PaymentMethodsList', {
    'payment_methods': fields.List(fields.Nested(payment_method_model),
                                    description='List of payment methods'),
    'count': fields.Integer(description='Number of payment methods')
})

validation_error_model = payment_methods_ns.model('ValidationError', {
    'errors': fields.List(fields.String, description='List of validation errors')
})


@payment_methods_ns.route('/')
class PaymentMethodList(Resource):
    @payment_methods_ns.doc('list_payment_methods',
                            description='Get all payment methods for the authenticated user',
                            security='Bearer Auth')
    @payment_methods_ns.marshal_with(payment_methods_list_model)
    @payment_methods_ns.param('include_inactive', 'Include inactive payment methods', type=bool, default=False)
    @jwt_required
    def get(self):
        """Get all payment methods for the current user"""
        try:
            user_id = g.current_user.id
            include_inactive = request.args.get('include_inactive', 'false').lower() == 'true'

            payment_methods = PaymentMethod.get_by_user_id(user_id, active_only=not include_inactive)
            payment_methods_dict = [pm.to_dict() for pm in payment_methods]

            return {
                'payment_methods': payment_methods_dict,
                'count': len(payment_methods_dict)
            }, 200

        except Exception as e:
            payment_methods_ns.abort(500, f'Failed to retrieve payment methods: {str(e)}')

    @payment_methods_ns.doc('create_payment_method',
                            description='Add a new payment method for the authenticated user',
                            security='Bearer Auth')
    @payment_methods_ns.expect(payment_method_create_model, validate=True)
    @payment_methods_ns.marshal_with(payment_method_model, code=201)
    @payment_methods_ns.response(400, 'Validation Error', validation_error_model)
    @jwt_required
    def post(self):
        """Add a new payment method"""
        try:
            user_id = g.current_user.id
            data = request.json

            if not data:
                payment_methods_ns.abort(400, 'No data provided')

            # Create payment method
            payment_method = PaymentMethod(
                user_id=user_id,
                method_type=data.get('method_type', PaymentMethod.TYPE_CREDIT_CARD),
                gateway=data.get('gateway', PaymentMethod.GATEWAY_STRIPE)
            )

            # Set gateway integration fields
            payment_method.gateway_customer_id = data.get('gateway_customer_id')
            payment_method.gateway_payment_method_id = data.get('gateway_payment_method_id')

            # Set card information
            payment_method.card_last_four = data.get('card_last_four')
            payment_method.card_brand = data.get('card_brand')
            payment_method.card_exp_month = data.get('card_exp_month')
            payment_method.card_exp_year = data.get('card_exp_year')
            payment_method.card_funding = data.get('card_funding')

            # Set PayPal information
            payment_method.paypal_email = data.get('paypal_email')

            # Set bank information
            payment_method.bank_name = data.get('bank_name')
            payment_method.bank_last_four = data.get('bank_last_four')
            payment_method.bank_account_type = data.get('bank_account_type')

            # Set billing information
            payment_method.billing_address_id = data.get('billing_address_id')
            payment_method.cardholder_name = data.get('cardholder_name')
            payment_method.nickname = data.get('nickname')

            # Validate payment method
            validation_errors = payment_method.validate()
            if validation_errors:
                return {'errors': validation_errors}, 400

            # Check if card is expired
            if payment_method.is_expired():
                return {'errors': ['Card has expired']}, 400

            # Save payment method
            payment_method.save()

            # Set as default if requested
            if data.get('is_default', False):
                payment_method.set_as_default()

            return payment_method.to_dict(), 201

        except Exception as e:
            payment_methods_ns.abort(500, f'Failed to create payment method: {str(e)}')


@payment_methods_ns.route('/<string:payment_method_id>')
@payment_methods_ns.param('payment_method_id', 'The payment method identifier')
class PaymentMethodItem(Resource):
    @payment_methods_ns.doc('get_payment_method',
                            description='Get a specific payment method by ID',
                            security='Bearer Auth')
    @payment_methods_ns.marshal_with(payment_method_model)
    @jwt_required
    def get(self, payment_method_id):
        """Get a payment method by ID"""
        try:
            user_id = g.current_user.id
            payment_method = PaymentMethod.get_by_id(payment_method_id)

            if not payment_method:
                payment_methods_ns.abort(404, 'Payment method not found')

            # Ensure payment method belongs to current user
            if payment_method.user_id != user_id:
                payment_methods_ns.abort(403, 'Access denied')

            return payment_method.to_dict(), 200

        except Exception as e:
            payment_methods_ns.abort(500, f'Failed to retrieve payment method: {str(e)}')

    @payment_methods_ns.doc('update_payment_method',
                            description='Update a payment method (limited fields for security)',
                            security='Bearer Auth')
    @payment_methods_ns.expect(payment_method_update_model, validate=False)
    @payment_methods_ns.marshal_with(payment_method_model)
    @jwt_required
    def put(self, payment_method_id):
        """Update a payment method (metadata only, not card details)"""
        try:
            user_id = g.current_user.id
            payment_method = PaymentMethod.get_by_id(payment_method_id)

            if not payment_method:
                payment_methods_ns.abort(404, 'Payment method not found')

            # Ensure payment method belongs to current user
            if payment_method.user_id != user_id:
                payment_methods_ns.abort(403, 'Access denied')

            data = request.json
            if not data:
                payment_methods_ns.abort(400, 'No data provided')

            # Only allow updating certain fields (not card details for security)
            if 'nickname' in data:
                payment_method.nickname = data['nickname']

            if 'billing_address_id' in data:
                payment_method.billing_address_id = data['billing_address_id']

            if 'cardholder_name' in data:
                payment_method.cardholder_name = data['cardholder_name']

            if 'is_active' in data:
                if data['is_active']:
                    payment_method.reactivate()
                else:
                    payment_method.deactivate()

            # Save updated payment method
            payment_method.save()

            # Handle default flag
            if 'is_default' in data and data['is_default']:
                payment_method.set_as_default()
            elif 'is_default' in data and not data['is_default']:
                payment_method.is_default = False
                payment_method.save()

            return payment_method.to_dict(), 200

        except Exception as e:
            payment_methods_ns.abort(500, f'Failed to update payment method: {str(e)}')

    @payment_methods_ns.doc('delete_payment_method',
                            description='Delete a payment method',
                            security='Bearer Auth')
    @jwt_required
    def delete(self, payment_method_id):
        """Delete a payment method"""
        try:
            user_id = g.current_user.id
            payment_method = PaymentMethod.get_by_id(payment_method_id)

            if not payment_method:
                payment_methods_ns.abort(404, 'Payment method not found')

            # Ensure payment method belongs to current user
            if payment_method.user_id != user_id:
                payment_methods_ns.abort(403, 'Access denied')

            # Instead of deleting, deactivate for audit trail
            # Users can choose to fully delete if needed
            if payment_method.delete():
                return {'message': 'Payment method deleted successfully'}, 200
            else:
                payment_methods_ns.abort(500, 'Failed to delete payment method')

        except Exception as e:
            payment_methods_ns.abort(500, f'Failed to delete payment method: {str(e)}')


@payment_methods_ns.route('/default')
class DefaultPaymentMethod(Resource):
    @payment_methods_ns.doc('get_default_payment_method',
                            description='Get the default payment method for the authenticated user',
                            security='Bearer Auth')
    @payment_methods_ns.marshal_with(payment_method_model)
    @jwt_required
    def get(self):
        """Get the default payment method"""
        try:
            user_id = g.current_user.id
            payment_method = PaymentMethod.get_default_by_user_id(user_id)

            if not payment_method:
                payment_methods_ns.abort(404, 'No default payment method found')

            return payment_method.to_dict(), 200

        except Exception as e:
            payment_methods_ns.abort(500, f'Failed to retrieve default payment method: {str(e)}')


@payment_methods_ns.route('/<string:payment_method_id>/set-default')
@payment_methods_ns.param('payment_method_id', 'The payment method identifier')
class SetDefaultPaymentMethod(Resource):
    @payment_methods_ns.doc('set_default_payment_method',
                            description='Set a payment method as the default',
                            security='Bearer Auth')
    @payment_methods_ns.marshal_with(payment_method_model)
    @jwt_required
    def put(self, payment_method_id):
        """Set a payment method as default"""
        try:
            user_id = g.current_user.id
            payment_method = PaymentMethod.get_by_id(payment_method_id)

            if not payment_method:
                payment_methods_ns.abort(404, 'Payment method not found')

            # Ensure payment method belongs to current user
            if payment_method.user_id != user_id:
                payment_methods_ns.abort(403, 'Access denied')

            # Cannot set inactive payment method as default
            if not payment_method.is_active:
                payment_methods_ns.abort(400, 'Cannot set inactive payment method as default')

            # Cannot set expired card as default
            if payment_method.is_expired():
                payment_methods_ns.abort(400, 'Cannot set expired card as default')

            # Set as default
            payment_method.set_as_default()

            return payment_method.to_dict(), 200

        except Exception as e:
            payment_methods_ns.abort(500, f'Failed to set default payment method: {str(e)}')


@payment_methods_ns.route('/<string:payment_method_id>/deactivate')
@payment_methods_ns.param('payment_method_id', 'The payment method identifier')
class DeactivatePaymentMethod(Resource):
    @payment_methods_ns.doc('deactivate_payment_method',
                            description='Deactivate a payment method (soft delete)',
                            security='Bearer Auth')
    @payment_methods_ns.marshal_with(payment_method_model)
    @jwt_required
    def put(self, payment_method_id):
        """Deactivate a payment method without deleting it"""
        try:
            user_id = g.current_user.id
            payment_method = PaymentMethod.get_by_id(payment_method_id)

            if not payment_method:
                payment_methods_ns.abort(404, 'Payment method not found')

            # Ensure payment method belongs to current user
            if payment_method.user_id != user_id:
                payment_methods_ns.abort(403, 'Access denied')

            payment_method.deactivate()
            payment_method.save()

            return payment_method.to_dict(), 200

        except Exception as e:
            payment_methods_ns.abort(500, f'Failed to deactivate payment method: {str(e)}')
