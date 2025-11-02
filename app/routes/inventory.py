from flask import request
from flask_restx import Namespace, Resource, fields
from app.models.product import Product
from app.models.inventory import InventoryTransaction
from app.middleware.auth import jwt_required, admin_required

inventory_ns = Namespace('inventory', description='Inventory management operations', path='/inventory')

# Define models for request/response documentation
transaction_model = inventory_ns.model('InventoryTransaction', {
    'id': fields.String(description='Transaction ID'),
    'product_id': fields.String(required=True, description='Product ID'),
    'quantity': fields.Integer(required=True, description='Quantity change (positive for increase, negative for decrease)'),
    'transaction_type': fields.String(required=True, description='Transaction type',
                                     enum=['sale', 'restock', 'adjustment', 'return', 'reservation', 'release']),
    'reference_id': fields.String(description='Reference ID (e.g., order_id)'),
    'notes': fields.String(description='Additional notes'),
    'created_by': fields.String(description='User ID who created the transaction'),
    'created_at': fields.DateTime(description='Creation timestamp')
})

adjust_stock_model = inventory_ns.model('AdjustStock', {
    'quantity': fields.Integer(required=True, description='New stock quantity to set'),
    'notes': fields.String(description='Reason for adjustment')
})

restock_model = inventory_ns.model('Restock', {
    'quantity': fields.Integer(required=True, description='Quantity to add to stock', min=1),
    'notes': fields.String(description='Notes about the restock')
})

stock_info_model = inventory_ns.model('StockInfo', {
    'product_id': fields.String(description='Product ID'),
    'product_name': fields.String(description='Product name'),
    'current_stock': fields.Integer(description='Current stock level'),
    'requires_selling_stock': fields.Boolean(description='Whether product requires stock tracking'),
    'track_quantity': fields.Boolean(description='Whether quantity tracking is enabled'),
    'low_stock': fields.Boolean(description='Whether stock is below threshold'),
    'low_stock_threshold': fields.Integer(description='Low stock threshold', default=10)
})

transaction_list_model = inventory_ns.model('TransactionList', {
    'transactions': fields.List(fields.Nested(transaction_model)),
    'total': fields.Integer(description='Total number of transactions')
})


@inventory_ns.route('/products/<string:product_id>')
@inventory_ns.param('product_id', 'The product identifier')
class ProductInventory(Resource):
    @inventory_ns.doc('get_product_stock_info',
                     description='Get current stock information for a product')
    @inventory_ns.marshal_with(stock_info_model)
    def get(self, product_id):
        """Get stock information for a product"""
        product = Product.get_by_id(product_id)

        if not product:
            inventory_ns.abort(404, 'Product not found')

        low_stock_threshold = 10
        is_low_stock = product.requires_selling_stock and product.stock < low_stock_threshold

        return {
            'product_id': product.id,
            'product_name': product.name,
            'current_stock': product.stock,
            'requires_selling_stock': product.requires_selling_stock,
            'track_quantity': product.track_quantity,
            'low_stock': is_low_stock,
            'low_stock_threshold': low_stock_threshold
        }, 200


@inventory_ns.route('/products/<string:product_id>/adjust')
@inventory_ns.param('product_id', 'The product identifier')
class AdjustProductStock(Resource):
    @inventory_ns.doc('adjust_product_stock',
                     description='Set stock to a specific quantity (admin only)',
                     security='Bearer Auth')
    @jwt_required
    @admin_required
    @inventory_ns.expect(adjust_stock_model, validate=True)
    @inventory_ns.marshal_with(stock_info_model)
    def post(self, product_id):
        """Adjust product stock to a specific quantity"""
        product = Product.get_by_id(product_id)

        if not product:
            inventory_ns.abort(404, 'Product not found')

        if not product.requires_selling_stock:
            inventory_ns.abort(400, 'This product does not require stock tracking')

        data = request.json
        new_quantity = data.get('quantity')
        notes = data.get('notes', 'Manual stock adjustment')

        if new_quantity < 0:
            inventory_ns.abort(400, 'Stock quantity cannot be negative')

        # Calculate the difference
        quantity_change = new_quantity - product.stock
        old_stock = product.stock

        # Update product stock
        product.stock = new_quantity
        product.save()

        # Log the adjustment
        if quantity_change != 0:
            from flask import g
            user_id = g.current_user.get('user_id') if hasattr(g, 'current_user') else None

            InventoryTransaction.create_adjustment_transaction(
                product_id=product_id,
                quantity=quantity_change,
                reason=f'{notes} (Changed from {old_stock} to {new_quantity})',
                created_by=user_id
            )

        low_stock_threshold = 10
        is_low_stock = product.requires_selling_stock and product.stock < low_stock_threshold

        return {
            'product_id': product.id,
            'product_name': product.name,
            'current_stock': product.stock,
            'requires_selling_stock': product.requires_selling_stock,
            'track_quantity': product.track_quantity,
            'low_stock': is_low_stock,
            'low_stock_threshold': low_stock_threshold
        }, 200


@inventory_ns.route('/products/<string:product_id>/restock')
@inventory_ns.param('product_id', 'The product identifier')
class RestockProduct(Resource):
    @inventory_ns.doc('restock_product',
                     description='Add stock to a product (admin only)',
                     security='Bearer Auth')
    @jwt_required
    @admin_required
    @inventory_ns.expect(restock_model, validate=True)
    @inventory_ns.marshal_with(stock_info_model)
    def post(self, product_id):
        """Add stock to a product (restock)"""
        product = Product.get_by_id(product_id)

        if not product:
            inventory_ns.abort(404, 'Product not found')

        if not product.requires_selling_stock:
            inventory_ns.abort(400, 'This product does not require stock tracking')

        data = request.json
        quantity = data.get('quantity')
        notes = data.get('notes', 'Stock replenished')

        if quantity <= 0:
            inventory_ns.abort(400, 'Quantity must be greater than 0')

        # Update product stock
        old_stock = product.stock
        product.stock += quantity
        product.save()

        # Log the restock
        from flask import g
        user_id = g.current_user.get('user_id') if hasattr(g, 'current_user') else None

        InventoryTransaction.create_restock_transaction(
            product_id=product_id,
            quantity=quantity,
            notes=f'{notes} (Added {quantity} units, stock: {old_stock} → {product.stock})',
            created_by=user_id
        )

        low_stock_threshold = 10
        is_low_stock = product.requires_selling_stock and product.stock < low_stock_threshold

        return {
            'product_id': product.id,
            'product_name': product.name,
            'current_stock': product.stock,
            'requires_selling_stock': product.requires_selling_stock,
            'track_quantity': product.track_quantity,
            'low_stock': is_low_stock,
            'low_stock_threshold': low_stock_threshold
        }, 200


@inventory_ns.route('/products/<string:product_id>/transactions')
@inventory_ns.param('product_id', 'The product identifier')
class ProductTransactions(Resource):
    @inventory_ns.doc('get_product_transactions',
                     description='Get inventory transaction history for a product (admin only)',
                     security='Bearer Auth')
    @jwt_required
    @admin_required
    @inventory_ns.param('limit', 'Maximum number of transactions to return', type=int)
    @inventory_ns.marshal_with(transaction_list_model)
    def get(self, product_id):
        """Get transaction history for a product"""
        product = Product.get_by_id(product_id)

        if not product:
            inventory_ns.abort(404, 'Product not found')

        limit = request.args.get('limit', type=int)

        transactions = InventoryTransaction.get_by_product(product_id, limit=limit)
        transactions_dict = [t.to_dict() for t in transactions]

        return {
            'transactions': transactions_dict,
            'total': len(transactions_dict)
        }, 200


@inventory_ns.route('/transactions')
class TransactionList(Resource):
    @inventory_ns.doc('get_all_transactions',
                     description='Get all inventory transactions (admin only)',
                     security='Bearer Auth')
    @jwt_required
    @admin_required
    @inventory_ns.param('limit', 'Maximum number of transactions to return', type=int)
    @inventory_ns.param('type', 'Filter by transaction type')
    @inventory_ns.marshal_with(transaction_list_model)
    def get(self):
        """Get all inventory transactions"""
        limit = request.args.get('limit', type=int)
        transaction_type = request.args.get('type')

        if transaction_type and transaction_type not in InventoryTransaction.TRANSACTION_TYPES:
            inventory_ns.abort(400, f'Invalid transaction type. Valid types: {", ".join(InventoryTransaction.TRANSACTION_TYPES)}')

        transactions = InventoryTransaction.get_all(limit=limit, transaction_type=transaction_type)
        transactions_dict = [t.to_dict() for t in transactions]

        return {
            'transactions': transactions_dict,
            'total': len(transactions_dict)
        }, 200


@inventory_ns.route('/low-stock')
class LowStockProducts(Resource):
    @inventory_ns.doc('get_low_stock_products',
                     description='Get products with low stock levels (admin only)',
                     security='Bearer Auth')
    @jwt_required
    @admin_required
    @inventory_ns.param('threshold', 'Low stock threshold', type=int, default=10)
    def get(self):
        """Get products with low stock"""
        threshold = request.args.get('threshold', 10, type=int)

        # Get all products that require stock tracking
        all_products = Product.get_all()
        low_stock_products = []

        for product in all_products:
            if product.requires_selling_stock and product.stock < threshold:
                low_stock_products.append({
                    'product_id': product.id,
                    'product_name': product.name,
                    'current_stock': product.stock,
                    'threshold': threshold,
                    'category_id': product.category_id
                })

        return {
            'products': low_stock_products,
            'total': len(low_stock_products),
            'threshold': threshold
        }, 200
