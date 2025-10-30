from flask import request, g
from flask_restx import Namespace, Resource, fields
from app.models.order import Order
from app.models.cart import Cart
from app.middleware.auth import jwt_required, optional_jwt
from app.middleware.guest_session import guest_session_handler, get_cart_identifier
from datetime import datetime, timezone

orders_ns = Namespace('orders', description='Order management operations', path='/orders')

# Define models for request/response documentation
order_item_model = orders_ns.model('OrderItem', {
    'id': fields.String(description='Order item ID'),
    'product_id': fields.String(description='Product ID'),
    'product_name': fields.String(description='Product name'),
    'quantity': fields.Integer(description='Quantity ordered'),
    'unit_price': fields.Float(description='Price per unit at time of purchase'),
    'variant': fields.Raw(description='Product variant details'),
    'total_price': fields.Float(description='Total price for this item')
})

address_model = orders_ns.model('Address', {
    'street': fields.String(description='Street address'),
    'city': fields.String(description='City'),
    'state': fields.String(description='State/Province'),
    'postal_code': fields.String(description='Postal/ZIP code'),
    'country': fields.String(description='Country'),
    'phone': fields.String(description='Phone number'),
    'email': fields.String(description='Email address (required for guest orders)')
})

order_model = orders_ns.model('Order', {
    'id': fields.String(description='Order ID'),
    'order_number': fields.String(description='Human-readable order number'),
    'user_id': fields.String(description='User ID'),
    'status': fields.String(description='Order status'),
    'items': fields.List(fields.Nested(order_item_model), description='Order items'),
    'item_count': fields.Integer(description='Number of unique items'),
    'total_quantity': fields.Integer(description='Total quantity of all items'),
    'subtotal': fields.Float(description='Order subtotal'),
    'tax': fields.Float(description='Tax amount'),
    'shipping': fields.Float(description='Shipping cost'),
    'discount': fields.Float(description='Discount amount'),
    'total': fields.Float(description='Order total'),
    'shipping_address': fields.Nested(address_model, description='Shipping address'),
    'billing_address': fields.Nested(address_model, description='Billing address'),
    'payment_method': fields.String(description='Payment method'),
    'payment_status': fields.String(description='Payment status'),
    'payment_id': fields.String(description='Payment transaction ID'),
    'customer_notes': fields.String(description='Customer notes'),
    'admin_notes': fields.String(description='Admin notes'),
    'tracking_number': fields.String(description='Shipping tracking number'),
    'created_at': fields.DateTime(description='Order creation timestamp'),
    'updated_at': fields.DateTime(description='Last update timestamp'),
    'paid_at': fields.DateTime(description='Payment timestamp'),
    'shipped_at': fields.DateTime(description='Shipping timestamp'),
    'delivered_at': fields.DateTime(description='Delivery timestamp'),
    'cancelled_at': fields.DateTime(description='Cancellation timestamp')
})

create_order_request_model = orders_ns.model('CreateOrderRequest', {
    'shipping_address': fields.Nested(address_model, required=False, description='Shipping address (required for guest orders with email and phone)'),
    'billing_address': fields.Nested(address_model, required=False, description='Billing address'),
    'customer_notes': fields.String(required=False, description='Customer notes or special instructions')
})

orders_list_model = orders_ns.model('OrdersList', {
    'orders': fields.List(fields.Nested(order_model), description='List of orders'),
    'total': fields.Integer(description='Total number of orders'),
    'page': fields.Integer(description='Current page'),
    'per_page': fields.Integer(description='Items per page')
})

stock_issue_model = orders_ns.model('StockIssue', {
    'item_id': fields.String(description='Item ID'),
    'product_id': fields.String(description='Product ID'),
    'product_name': fields.String(description='Product name'),
    'requested_quantity': fields.Integer(description='Requested quantity'),
    'available_stock': fields.Integer(description='Available stock'),
    'issue': fields.String(description='Issue description')
})


@orders_ns.route('/')
class OrderList(Resource):
    @orders_ns.doc('list_orders',
                   description='Get all orders for the current user or guest with pagination.')
    @orders_ns.marshal_with(orders_list_model)
    @orders_ns.param('page', 'Page number', type=int, default=1)
    @orders_ns.param('per_page', 'Items per page', type=int, default=10)
    @orders_ns.param('status', 'Filter by order status')
    @optional_jwt
    @guest_session_handler
    def get(self):
        """Get user's orders (authenticated or guest)"""
        try:
            # Get cart identifier (user_id or guest_session_id)
            cart_id, is_authenticated = get_cart_identifier()

            page = request.args.get('page', 1, type=int)
            per_page = request.args.get('per_page', 10, type=int)
            status_filter = request.args.get('status', '').strip()

            # Validate pagination
            if page < 1:
                orders_ns.abort(400, 'Page must be greater than 0')
            if per_page < 1 or per_page > 100:
                orders_ns.abort(400, 'Per page must be between 1 and 100')

            # Validate status if provided
            if status_filter:
                valid_statuses = [
                    Order.STATUS_PENDING,
                    Order.STATUS_PROCESSING,
                    Order.STATUS_SHIPPED,
                    Order.STATUS_DELIVERED,
                    Order.STATUS_CANCELLED,
                    Order.STATUS_REFUNDED
                ]
                if status_filter not in valid_statuses:
                    orders_ns.abort(400, f'Invalid status. Valid options: {", ".join(valid_statuses)}')

            # Calculate offset
            offset = (page - 1) * per_page

            # Get orders (works for both authenticated users and guests)
            all_orders = Order.get_by_user_id(cart_id)

            # Filter by status if provided
            if status_filter:
                all_orders = [order for order in all_orders if order.status == status_filter]

            total_orders = len(all_orders)

            # Apply pagination
            paginated_orders = all_orders[offset:offset + per_page]

            # Convert to dict
            orders_dict = [order.to_dict() for order in paginated_orders]

            return {
                'orders': orders_dict,
                'total': total_orders,
                'page': page,
                'per_page': per_page
            }, 200

        except Exception as e:
            orders_ns.abort(500, f'Failed to retrieve orders: {str(e)}')

    @orders_ns.doc('create_order',
                   description='Create a new order from cart. Works for both authenticated users and guests. Guest orders require shipping address with email and phone.')
    @orders_ns.expect(create_order_request_model, validate=False)
    @orders_ns.marshal_with(order_model, code=201)
    @optional_jwt
    @guest_session_handler
    def post(self):
        """Create order from cart (authenticated or guest)"""
        try:
            data = request.json or {}

            # Get cart identifier (user_id or guest_session_id)
            cart_id, is_authenticated = get_cart_identifier()

            # Get cart
            cart = Cart.get_by_user_id(cart_id)

            if not cart:
                orders_ns.abort(404, 'Cart not found')

            if cart.is_empty():
                orders_ns.abort(400, 'Cannot create order from empty cart')

            # Validate guest order requirements
            if not is_authenticated:
                # For guest orders, require shipping address with email and phone
                if 'shipping_address' not in data:
                    orders_ns.abort(400, 'Guest orders require shipping_address')

                shipping_addr = data['shipping_address']

                # Validate required fields for guest orders
                required_fields = ['street', 'city', 'state', 'postal_code', 'country', 'phone', 'email']
                missing_fields = [field for field in required_fields if not shipping_addr.get(field)]

                if missing_fields:
                    orders_ns.abort(400, f'Guest orders require the following fields in shipping_address: {", ".join(missing_fields)}')

                # Basic email validation
                email = shipping_addr.get('email', '').strip()
                if not email or '@' not in email:
                    orders_ns.abort(400, 'Valid email address is required for guest orders')

            # Validate cart items stock
            stock_issues = cart.validate_items_stock()
            if stock_issues:
                orders_ns.abort(400, f'Stock validation failed: {stock_issues}')

            # Create order from cart (using cart_id which can be user_id or guest_session_id)
            order = Order.create_from_cart(cart, user_id=cart_id)

            # Add addresses if provided
            if 'shipping_address' in data:
                order.shipping_address = data['shipping_address']

            if 'billing_address' in data:
                order.billing_address = data['billing_address']
            elif 'shipping_address' in data:
                # Use shipping address as billing if not provided
                order.billing_address = data['shipping_address']

            # Add customer notes if provided
            if 'customer_notes' in data:
                order.customer_notes = data['customer_notes']

            # Save order
            order.save()

            # Reduce stock for all products in order
            stock_reduction_issues = order.reduce_product_stock()
            if stock_reduction_issues:
                # Log issues but don't fail the order
                # In production, you might want to handle this differently
                print(f"Warning: Stock reduction issues for order {order.order_number}: {stock_reduction_issues}")

            # Mark cart as checked out and clear it
            cart.mark_as_checked_out()
            cart.save()

            return order.to_dict(), 201

        except Exception as e:
            orders_ns.abort(500, f'Failed to create order: {str(e)}')


@orders_ns.route('/<string:order_id>')
@orders_ns.param('order_id', 'The order identifier')
class OrderDetail(Resource):
    @orders_ns.doc('get_order',
                   description='Get order details by ID. Users and guests can only view their own orders.')
    @orders_ns.marshal_with(order_model)
    @optional_jwt
    @guest_session_handler
    def get(self, order_id):
        """Get order details (authenticated or guest)"""
        try:
            # Get cart identifier (user_id or guest_session_id)
            cart_id, is_authenticated = get_cart_identifier()

            # Get order
            order = Order.get_by_id(order_id)

            if not order:
                orders_ns.abort(404, 'Order not found')

            # Verify user/guest owns this order
            if order.user_id != cart_id:
                orders_ns.abort(403, 'You do not have permission to view this order')

            return order.to_dict(), 200

        except Exception as e:
            orders_ns.abort(500, f'Failed to retrieve order: {str(e)}')


@orders_ns.route('/<string:order_id>/cancel')
@orders_ns.param('order_id', 'The order identifier')
class OrderCancel(Resource):
    @orders_ns.doc('cancel_order',
                   description='Cancel an order. Only orders in pending or processing status can be cancelled. Works for both authenticated users and guests.')
    @orders_ns.marshal_with(order_model)
    @optional_jwt
    @guest_session_handler
    def post(self, order_id):
        """Cancel order (authenticated or guest)"""
        try:
            # Get cart identifier (user_id or guest_session_id)
            cart_id, is_authenticated = get_cart_identifier()

            # Get order
            order = Order.get_by_id(order_id)

            if not order:
                orders_ns.abort(404, 'Order not found')

            # Verify user/guest owns this order
            if order.user_id != cart_id:
                orders_ns.abort(403, 'You do not have permission to cancel this order')

            # Check if order can be cancelled
            if not order.can_cancel():
                orders_ns.abort(400, f'Cannot cancel order with status: {order.status}')

            # Cancel order
            order.mark_as_cancelled(reason='Cancelled by customer')
            order.save()

            return order.to_dict(), 200

        except Exception as e:
            orders_ns.abort(500, f'Failed to cancel order: {str(e)}')


@orders_ns.route('/number/<string:order_number>')
@orders_ns.param('order_number', 'The order number (e.g., ORD-20251029-ABC123)')
class OrderByNumber(Resource):
    @orders_ns.doc('get_order_by_number',
                   security='Bearer',
                   description='Get order details by order number. Users can only view their own orders.')
    @orders_ns.marshal_with(order_model)
    @jwt_required
    def get(self, order_number):
        """Get order by order number (authenticated users)"""
        try:
            user = g.current_user

            # Get order
            order = Order.get_by_order_number(order_number)

            if not order:
                orders_ns.abort(404, 'Order not found')

            # Verify user owns this order
            if order.user_id != user.id:
                orders_ns.abort(403, 'You do not have permission to view this order')

            return order.to_dict(), 200

        except Exception as e:
            orders_ns.abort(500, f'Failed to retrieve order: {str(e)}')


# Guest order lookup model
guest_order_lookup_model = orders_ns.model('GuestOrderLookup', {
    'email': fields.String(required=True, description='Email address used when placing the order')
})


@orders_ns.route('/guest/<string:order_number>')
@orders_ns.param('order_number', 'The order number (e.g., ORD-20251029-ABC123)')
class GuestOrderLookup(Resource):
    @orders_ns.doc('get_guest_order',
                   description='Get order details for guest orders by order number and email verification.')
    @orders_ns.expect(guest_order_lookup_model, validate=True)
    @orders_ns.marshal_with(order_model)
    def post(self, order_number):
        """Get guest order by order number + email verification"""
        try:
            data = request.json
            email = data.get('email', '').strip().lower()

            if not email:
                orders_ns.abort(400, 'Email is required')

            # Get order
            order = Order.get_by_order_number(order_number)

            if not order:
                orders_ns.abort(404, 'Order not found')

            # Check if this is a guest order (user_id starts with 'guest_')
            if not order.user_id.startswith('guest_'):
                orders_ns.abort(403, 'This endpoint is only for guest orders. Please log in to view your order.')

            # Verify email matches the order's shipping address email
            order_email = order.shipping_address.get('email', '').strip().lower()

            if not order_email or order_email != email:
                orders_ns.abort(403, 'Email does not match order records')

            return order.to_dict(), 200

        except Exception as e:
            orders_ns.abort(500, f'Failed to retrieve order: {str(e)}')
