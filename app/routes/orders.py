from flask import request, g
from flask_restx import Namespace, Resource, fields
from app.models.order import Order
from app.models.cart import Cart
from app.middleware.auth import jwt_required
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
    'phone': fields.String(description='Phone number')
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
    'shipping_address': fields.Nested(address_model, required=False, description='Shipping address'),
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
                   security='Bearer',
                   description='Get all orders for the current user with pagination.')
    @orders_ns.marshal_with(orders_list_model)
    @orders_ns.param('page', 'Page number', type=int, default=1)
    @orders_ns.param('per_page', 'Items per page', type=int, default=10)
    @orders_ns.param('status', 'Filter by order status')
    @jwt_required
    def get(self):
        """Get user's orders"""
        try:
            user = g.current_user
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

            # Get user's orders
            all_orders = Order.get_by_user_id(user.id)

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
                   security='Bearer',
                   description='Create a new order from the current user\'s cart.')
    @orders_ns.expect(create_order_request_model, validate=False)
    @orders_ns.marshal_with(order_model, code=201)
    @jwt_required
    def post(self):
        """Create order from cart"""
        try:
            user = g.current_user
            data = request.json or {}

            # Get user's cart
            cart = Cart.get_by_user_id(user.id)

            if not cart:
                orders_ns.abort(404, 'Cart not found')

            if cart.is_empty():
                orders_ns.abort(400, 'Cannot create order from empty cart')

            # Validate cart items stock
            stock_issues = cart.validate_items_stock()
            if stock_issues:
                orders_ns.abort(400, f'Stock validation failed: {stock_issues}')

            # Create order from cart
            order = Order.create_from_cart(cart, user_id=user.id)

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
                   security='Bearer',
                   description='Get order details by ID. Users can only view their own orders.')
    @orders_ns.marshal_with(order_model)
    @jwt_required
    def get(self, order_id):
        """Get order details"""
        try:
            user = g.current_user

            # Get order
            order = Order.get_by_id(order_id)

            if not order:
                orders_ns.abort(404, 'Order not found')

            # Verify user owns this order
            if order.user_id != user.id:
                orders_ns.abort(403, 'You do not have permission to view this order')

            return order.to_dict(), 200

        except Exception as e:
            orders_ns.abort(500, f'Failed to retrieve order: {str(e)}')


@orders_ns.route('/<string:order_id>/cancel')
@orders_ns.param('order_id', 'The order identifier')
class OrderCancel(Resource):
    @orders_ns.doc('cancel_order',
                   security='Bearer',
                   description='Cancel an order. Only orders in pending or processing status can be cancelled.')
    @orders_ns.marshal_with(order_model)
    @jwt_required
    def post(self, order_id):
        """Cancel order"""
        try:
            user = g.current_user

            # Get order
            order = Order.get_by_id(order_id)

            if not order:
                orders_ns.abort(404, 'Order not found')

            # Verify user owns this order
            if order.user_id != user.id:
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
        """Get order by order number"""
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
