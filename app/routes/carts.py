from flask import request, g
from flask_restx import Namespace, Resource, fields
from app.models.cart import Cart
from app.models.product import Product
from app.middleware.auth import jwt_required, optional_jwt
from app.middleware.guest_session import guest_session_handler, get_cart_identifier

carts_ns = Namespace('carts', description='Shopping cart operations', path='/carts')


def get_or_create_cart():
    """
    Get or create cart for current user or guest session.
    Returns tuple: (cart, is_authenticated)
    """
    cart_id, is_authenticated = get_cart_identifier()

    if is_authenticated:
        # Get or create cart for authenticated user
        cart = Cart.get_or_create_for_user(cart_id)
    else:
        # Get or create cart for guest
        # For guests, we need to find cart by searching for carts with user_id = guest_session_id
        cart = Cart.get_by_user_id(cart_id)
        if not cart:
            # Create new guest cart
            cart = Cart(user_id=cart_id)
            cart.save()

    return cart, is_authenticated

# Define models for request/response documentation
cart_item_variant_model = carts_ns.model('CartItemVariant', {
    'option_name': fields.String(description='Variant option name (e.g., "Size", "Color")'),
    'option_value': fields.String(description='Variant option value (e.g., "Large", "Red")')
})

cart_item_model = carts_ns.model('CartItem', {
    'id': fields.String(description='Cart item ID'),
    'product_id': fields.String(required=True, description='Product ID'),
    'product_name': fields.String(description='Product name'),
    'quantity': fields.Integer(required=True, description='Quantity', min=1),
    'price_at_addition': fields.Float(description='Price when added to cart'),
    'variant': fields.Raw(description='Product variant details'),
    'added_at': fields.DateTime(description='When item was added to cart')
})

add_item_request_model = carts_ns.model('AddItemRequest', {
    'product_id': fields.String(required=True, description='Product ID'),
    'quantity': fields.Integer(required=True, description='Quantity to add', min=1, default=1),
    'variant': fields.Raw(description='Product variant details (optional)')
})

update_item_request_model = carts_ns.model('UpdateItemRequest', {
    'quantity': fields.Integer(required=True, description='New quantity', min=0)
})

cart_summary_model = carts_ns.model('CartSummary', {
    'id': fields.String(description='Cart ID'),
    'user_id': fields.String(description='User ID (null for guest carts)'),
    'status': fields.String(description='Cart status'),
    'items': fields.List(fields.Nested(cart_item_model), description='Cart items'),
    'item_count': fields.Integer(description='Number of unique items'),
    'total_quantity': fields.Integer(description='Total quantity of all items'),
    'subtotal': fields.Float(description='Cart subtotal'),
    'created_at': fields.DateTime(description='Cart creation timestamp'),
    'updated_at': fields.DateTime(description='Last update timestamp'),
    'expires_at': fields.DateTime(description='Expiration timestamp (for guest carts)')
})

stock_issue_model = carts_ns.model('StockIssue', {
    'item_id': fields.String(description='Cart item ID'),
    'product_id': fields.String(description='Product ID'),
    'product_name': fields.String(description='Product name'),
    'requested_quantity': fields.Integer(description='Requested quantity'),
    'available_stock': fields.Integer(description='Available stock'),
    'issue': fields.String(description='Issue description')
})

cart_validation_model = carts_ns.model('CartValidation', {
    'valid': fields.Boolean(description='Whether cart is valid'),
    'issues': fields.List(fields.Nested(stock_issue_model), description='Stock issues found'),
    'message': fields.String(description='Validation message')
})


@carts_ns.route('/mine')
class MyCart(Resource):
    @carts_ns.doc('get_my_cart',
                  description='Get the current cart. Works for both authenticated users and guests.')
    @carts_ns.marshal_with(cart_summary_model)
    @optional_jwt
    @guest_session_handler
    def get(self):
        """Get current cart (user or guest)"""
        try:
            cart, _ = get_or_create_cart()
            res = cart.to_dict(), 200
            return res

        except Exception as e:
            carts_ns.abort(500, f'Failed to retrieve cart: {str(e)}')

    @carts_ns.doc('clear_my_cart',
                  description='Clear all items from the current cart.')
    @optional_jwt
    @guest_session_handler
    def delete(self):
        """Clear all items from cart"""
        try:
            cart, _ = get_or_create_cart()
            cart.clear_items()
            cart.save()

            return {'message': 'Cart cleared successfully'}, 200

        except Exception as e:
            carts_ns.abort(500, f'Failed to clear cart: {str(e)}')


@carts_ns.route('/items')
class CartItems(Resource):
    @carts_ns.doc('add_item_to_cart',
                  description='Add an item to the cart. Works for both authenticated users and guests.')
    @carts_ns.expect(add_item_request_model, validate=True)
    @carts_ns.marshal_with(cart_summary_model)
    @optional_jwt
    @guest_session_handler
    def post(self):
        """Add item to cart"""
        try:
            data = request.json

            # Validate product exists
            product = Product.get_by_id(data['product_id'])
            if not product:
                carts_ns.abort(404, 'Product not found')

            # Validate quantity
            quantity = data.get('quantity', 1)
            if quantity < 1:
                carts_ns.abort(400, 'Quantity must be at least 1')

            # Check stock if product tracks quantity
            if product.track_quantity and product.requires_selling_stock:
                if product.stock < quantity:
                    carts_ns.abort(400, f'Insufficient stock. Available: {product.stock}')

            # Get or create cart
            cart, _ = get_or_create_cart()

            # Add item to cart
            variant = data.get('variant')
            cart.add_item(
                product_id=product.id,
                product_name=product.name,
                price=product.price,
                quantity=quantity,
                variant=variant
            )

            cart.save()

            return cart.to_dict(), 201

        except Exception as e:
            carts_ns.abort(500, f'Failed to add item to cart: {str(e)}')


@carts_ns.route('/items/<string:item_id>')
@carts_ns.param('item_id', 'The cart item identifier')
class CartItemResource(Resource):
    @carts_ns.doc('update_cart_item',
                  description='Update cart item quantity. Set quantity to 0 to remove item.')
    @carts_ns.expect(update_item_request_model, validate=True)
    @carts_ns.marshal_with(cart_summary_model)
    @optional_jwt
    @guest_session_handler
    def put(self, item_id):
        """Update cart item quantity"""
        try:
            data = request.json
            new_quantity = data['quantity']

            # Get cart
            cart, _ = get_or_create_cart()

            # Find the item
            item = None
            for cart_item in cart.items:
                if cart_item.id == item_id:
                    item = cart_item
                    break

            if not item:
                carts_ns.abort(404, 'Cart item not found')

            # Validate new quantity against stock
            if new_quantity > 0:
                product = Product.get_by_id(item.product_id)
                if product and product.track_quantity and product.requires_selling_stock:
                    if product.stock < new_quantity:
                        carts_ns.abort(400, f'Insufficient stock. Available: {product.stock}')

            # Update quantity (will remove if quantity is 0)
            if new_quantity == 0:
                cart.remove_item(item_id)
            else:
                cart.update_item_quantity(item_id, new_quantity)

            cart.save()

            return cart.to_dict(), 200

        except Exception as e:
            carts_ns.abort(500, f'Failed to update cart item: {str(e)}')

    @carts_ns.doc('remove_cart_item',
                  description='Remove an item from the cart.')
    @carts_ns.marshal_with(cart_summary_model)
    @optional_jwt
    @guest_session_handler
    def delete(self, item_id):
        """Remove item from cart"""
        try:
            cart, _ = get_or_create_cart()

            if not cart.remove_item(item_id):
                carts_ns.abort(404, 'Cart item not found')

            cart.save()

            return cart.to_dict(), 200

        except Exception as e:
            carts_ns.abort(500, f'Failed to remove item from cart: {str(e)}')


@carts_ns.route('/validate')
class CartValidation(Resource):
    @carts_ns.doc('validate_cart',
                  description='Validate cart items against current product stock.')
    @carts_ns.marshal_with(cart_validation_model)
    @optional_jwt
    @guest_session_handler
    def post(self):
        """Validate cart items (stock availability)"""
        try:
            cart, _ = get_or_create_cart()

            if cart.is_empty():
                return {
                    'valid': False,
                    'issues': [],
                    'message': 'Cart is empty'
                }, 200

            # Validate stock
            issues = cart.validate_items_stock()

            if issues:
                return {
                    'valid': False,
                    'issues': issues,
                    'message': f'Found {len(issues)} item(s) with stock issues'
                }, 200

            return {
                'valid': True,
                'issues': [],
                'message': 'Cart is valid'
            }, 200

        except Exception as e:
            carts_ns.abort(500, f'Failed to validate cart: {str(e)}')


@carts_ns.route('/merge')
class CartMerge(Resource):
    @carts_ns.doc('merge_guest_cart',
                  security='Bearer',
                  description='Merge guest cart into user cart after login. Guest cart items are added to user cart.')
    @carts_ns.marshal_with(cart_summary_model)
    @jwt_required
    @guest_session_handler
    def post(self):
        """Merge guest cart into user cart"""
        try:
            user = g.current_user
            guest_session_id = g.guest_session_id

            # Get user's cart
            user_cart = Cart.get_or_create_for_user(user.id)

            # Get guest cart (if exists)
            guest_cart = Cart.get_by_user_id(guest_session_id)

            if not guest_cart or guest_cart.is_empty():
                # No guest cart or empty, just return user cart
                return user_cart.to_dict(), 200

            # Merge guest cart items into user cart
            merged_count = 0
            for guest_item in guest_cart.items:
                # Check if item exists in user cart
                existing_item = user_cart.find_item(guest_item.product_id, guest_item.variant)

                if existing_item:
                    # Update quantity
                    existing_item.quantity += guest_item.quantity
                else:
                    # Add new item
                    user_cart.add_item(
                        product_id=guest_item.product_id,
                        product_name=guest_item.product_name,
                        price=guest_item.price_at_addition,
                        quantity=guest_item.quantity,
                        variant=guest_item.variant
                    )
                merged_count += 1

            # Save user cart
            user_cart.save()

            # Clear guest cart
            guest_cart.clear_items()
            guest_cart.mark_as_checked_out()  # Mark as checked out to archive it
            guest_cart.save()

            return user_cart.to_dict(), 200

        except Exception as e:
            carts_ns.abort(500, f'Failed to merge carts: {str(e)}')
