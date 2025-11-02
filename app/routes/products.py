from flask import request
from flask_restx import Namespace, Resource, fields
from app.models.product import Product
from app.middleware.auth import jwt_required, admin_required
from datetime import datetime, timezone

products_ns = Namespace('products', description='Product operations', path='/products')

# Define models for request/response documentation
media_model = products_ns.model('ProductMedia', {
    'alt_text': fields.String(required=True, description='Alternative text for the media'),
    'url': fields.String(required=True, description='URL to the media file')
})

variant_model = products_ns.model('ProductVariant', {
    'option_name': fields.String(required=True, description='Variant option name (e.g., "Color", "Size", "Scent")'),
    'option_values': fields.List(fields.String, required=True, description='Available option values (e.g., ["Red", "Blue", "Green"])')
})
product_model = products_ns.model('Product', {
    'id': fields.String(description='Product ID'),
    'name': fields.String(required=True, description='Product name'),
    'description': fields.String(required=True, description='Product description'),
    'media': fields.List(fields.Nested(media_model), description='Media files'),
    'price': fields.Float(required=True, description='Product price'),
    'track_quantity': fields.Boolean(description='Whether to track quantity'),
    'weight': fields.Float(description='Product weight'),
    'size': fields.String(description='Product size'),
    'variants': fields.List(fields.Nested(variant_model), description='Product variants with option names and values'),
    'category_id': fields.String(description='Category ID'),
    'category': fields.Raw(description='Category details (when included)'),
    'stock': fields.Integer(description='Stock quantity'),
    'requires_selling_stock': fields.Boolean(description='Whether selling stock is required'),
    'related_product_ids': fields.List(fields.String, description='IDs of related/recommended products'),
    'related_products': fields.List(fields.Raw, description='Full related product details (when included)'),
    'created_at': fields.DateTime(description='Creation timestamp'),
    'updated_at': fields.DateTime(description='Last update timestamp')
})

product_create_model = products_ns.model('ProductCreate', {
    'name': fields.String(required=True, description='Product name'),
    'description': fields.String(required=True, description='Product description'),
    'media': fields.List(fields.Nested(media_model), description='Media files'),
    'price': fields.Float(required=True, description='Product price'),
    'track_quantity': fields.Boolean(description='Whether to track quantity', default=True),
    'weight': fields.Float(description='Product weight'),
    'size': fields.String(description='Product size'),
    'variants': fields.List(fields.Nested(variant_model), description='Product variants with option names and values'),
    'category_id': fields.String(required=True, description='Category ID'),
    'stock': fields.Integer(description='Stock quantity', default=0),
    'requires_selling_stock': fields.Boolean(description='Whether selling stock is required', default=False)
})

product_update_model = products_ns.model('ProductUpdate', {
    'name': fields.String(description='Product name'),
    'description': fields.String(description='Product description'),
    'media': fields.List(fields.Nested(media_model), description='Media files'),
    'price': fields.Float(description='Product price'),
    'track_quantity': fields.Boolean(description='Whether to track quantity'),
    'weight': fields.Float(description='Product weight'),
    'size': fields.String(description='Product size'),
    'variants': fields.List(fields.Nested(variant_model), description='Product variants with option names and values'),
    'category_id': fields.String(description='Category ID'),
    'stock': fields.Integer(description='Stock quantity'),
    'requires_selling_stock': fields.Boolean(description='Whether selling stock is required')
})

pagination_model = products_ns.model('Pagination', {
    'page': fields.Integer(description='Current page'),
    'per_page': fields.Integer(description='Items per page'),
    'total': fields.Integer(description='Total items'),
    'total_pages': fields.Integer(description='Total pages'),
    'has_next': fields.Boolean(description='Has next page'),
    'has_prev': fields.Boolean(description='Has previous page')
})

products_list_model = products_ns.model('ProductsList', {
    'products': fields.List(fields.Nested(product_model), description='List of products'),
    'pagination': fields.Nested(pagination_model, description='Pagination info'),
    'search': fields.String(description='Search term used'),
    'sort': fields.Raw(description='Sort parameters')
})


@products_ns.route('/')
class ProductList(Resource):
    @products_ns.doc('list_products')
    @products_ns.marshal_with(products_list_model)
    @products_ns.param('page', 'Page number', type=int, default=1)
    @products_ns.param('per_page', 'Items per page', type=int, default=10)
    @products_ns.param('search', 'Search term')
    @products_ns.param('sort_by', 'Sort field (created_at, name, price, category)')
    @products_ns.param('sort_order', 'Sort order (asc, desc)', default='asc')
    @products_ns.param('category_id', 'Filter by category ID')
    @products_ns.param('include_category', 'Include category details in response', type=bool, default=False)
    def get(self):
        """Get all products with pagination, search, and sorting"""
        try:
            page = request.args.get('page', 1, type=int)
            per_page = request.args.get('per_page', 10, type=int)
            search = request.args.get('search', '').strip()
            sort_by = request.args.get('sort_by', '').strip()
            sort_order = request.args.get('sort_order', 'asc').strip().lower()
            category_id = request.args.get('category_id', '').strip()
            include_category = request.args.get('include_category', 'false').lower() == 'true'

            if page < 1:
                products_ns.abort(400, 'Page must be greater than 0')
            if per_page < 1 or per_page > 100:
                products_ns.abort(400, 'Per page must be between 1 and 100')

            valid_sort_fields = ['created_at', 'name', 'price', 'category']
            if sort_by and sort_by not in valid_sort_fields:
                products_ns.abort(400, f'Invalid sort field. Valid options: {", ".join(valid_sort_fields)}')

            if sort_order not in ['asc', 'desc']:
                products_ns.abort(400, 'Sort order must be "asc" or "desc"')

            # Validate category exists if provided
            if category_id:
                from app.models.category import Category
                category = Category.get_by_id(category_id)
                if not category:
                    products_ns.abort(400, 'Category not found')

            search_term = search if search else None
            sort_field = sort_by if sort_by else None
            category_filter = category_id if category_id else None
            offset = (page - 1) * per_page

            products = Product.get_all(
                limit=per_page,
                offset=offset,
                search=search_term,
                sort_by=sort_field,
                sort_order=sort_order,
                category_id=category_filter
            )
            total_products = Product.count(search=search_term, category_id=category_filter)
            products_dict = [product.to_dict(include_category=include_category) for product in products]

            total_pages = (total_products + per_page - 1) // per_page

            response_data = {
                'products': products_dict,
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': total_products,
                    'total_pages': total_pages,
                    'has_next': page < total_pages,
                    'has_prev': page > 1
                }
            }

            if search_term:
                response_data['search'] = search_term
            if sort_field:
                response_data['sort'] = {'by': sort_field, 'order': sort_order}

            return response_data, 200

        except Exception:
            products_ns.abort(500, 'Failed to retrieve products')

    @products_ns.doc('create_product',
                     description='Create a new product (admin only)',
                     security='Bearer Auth')
    @jwt_required
    @admin_required
    @products_ns.expect(product_create_model, validate=True)
    @products_ns.marshal_with(product_model, code=201)
    def post(self):
        """Create a new product (admin only)"""
        data = request.json

        if not data:
            products_ns.abort(400, 'No data provided')

        # Validate price is positive
        if data['price'] <= 0:
            products_ns.abort(400, 'Price must be greater than 0')

        # Validate stock if provided
        stock = data.get('stock', 0)
        if stock < 0:
            products_ns.abort(400, 'Stock cannot be negative')

        # Validate category exists
        from app.models.category import Category
        category = Category.get_by_id(data['category_id'])
        if not category:
            products_ns.abort(400, 'Category not found')
        if not category.is_active:
            products_ns.abort(400, 'Category is not active')

        try:
            product = Product(
                name=data['name'],
                description=data['description'],
                media=data.get('media', []),
                price=data['price'],
                track_quantity=data.get('track_quantity', True),
                weight=data.get('weight'),
                size=data.get('size'),
                variants=data.get('variants', []),
                category_id=data['category_id'],
                stock=stock,
                requires_selling_stock=data.get('requires_selling_stock', False)
            )

            product.save()
            return product.to_dict(), 201

        except Exception:
            products_ns.abort(500, 'Failed to create product')


@products_ns.route('/<string:product_id>')
@products_ns.param('product_id', 'The product identifier')
class ProductItem(Resource):
    @products_ns.doc('get_product')
    @products_ns.marshal_with(product_model)
    def get(self, product_id):
        """Get a product by ID"""
        try:
            product = Product.get_by_id(product_id)

            if not product:
                products_ns.abort(404, 'Product not found')

            return product.to_dict(), 200

        except Exception:
            products_ns.abort(500, 'Failed to retrieve product')

    @products_ns.doc('update_product',
                     description='Update a product (admin only)',
                     security='Bearer Auth')
    @jwt_required
    @admin_required
    @products_ns.expect(product_update_model, validate=False)
    @products_ns.marshal_with(product_model)
    def put(self, product_id):
        """Update a product (admin only)"""
        try:
            product = Product.get_by_id(product_id)

            if not product:
                products_ns.abort(404, 'Product not found')

            data = request.json
            if not data:
                products_ns.abort(400, 'No data provided')

            # Update fields if provided
            if 'name' in data:
                if not data['name']:
                    products_ns.abort(400, 'Name cannot be empty')
                product.name = data['name']

            if 'description' in data:
                if not data['description']:
                    products_ns.abort(400, 'Description cannot be empty')
                product.description = data['description']

            if 'price' in data:
                if data['price'] <= 0:
                    products_ns.abort(400, 'Price must be greater than 0')
                product.price = data['price']

            if 'category_id' in data:
                if not data['category_id']:
                    products_ns.abort(400, 'Category ID cannot be empty')
                # Validate category exists
                from app.models.category import Category
                category = Category.get_by_id(data['category_id'])
                if not category:
                    products_ns.abort(400, 'Category not found')
                if not category.is_active:
                    products_ns.abort(400, 'Category is not active')
                product.category_id = data['category_id']

            if 'stock' in data:
                if data['stock'] < 0:
                    products_ns.abort(400, 'Stock cannot be negative')
                product.stock = data['stock']

            if 'media' in data:
                product.media = data['media']

            if 'track_quantity' in data:
                product.track_quantity = data['track_quantity']

            if 'weight' in data:
                product.weight = data['weight']

            if 'size' in data:
                product.size = data['size']

            if 'variants' in data:
                product.variants = data['variants']

            if 'requires_selling_stock' in data:
                product.requires_selling_stock = data['requires_selling_stock']

            # Update timestamp
            product.updated_at = datetime.now(timezone.utc)

            product.save()
            return product.to_dict(), 200

        except Exception:
            products_ns.abort(500, 'Failed to update product')

    @products_ns.doc('delete_product',
                     description='Delete a product (admin only)',
                     security='Bearer Auth')
    @jwt_required
    @admin_required
    def delete(self, product_id):
        """Delete a product (admin only)"""
        try:
            product = Product.get_by_id(product_id)

            if not product:
                products_ns.abort(404, 'Product not found')

            if product.delete():
                return {'message': 'Product deleted successfully'}, 200
            else:
                products_ns.abort(500, 'Failed to delete product')

        except Exception:
            products_ns.abort(500, 'Failed to delete product')


# Related products model
related_products_model = products_ns.model('RelatedProducts', {
    'product_ids': fields.List(fields.String, required=True, description='List of related product IDs')
})


@products_ns.route('/<string:product_id>/related')
@products_ns.param('product_id', 'The product identifier')
class ProductRelated(Resource):
    @products_ns.doc('get_related_products',
                     description='Get related/recommended products for a specific product')
    @products_ns.marshal_with(products_list_model)
    @products_ns.param('limit', 'Maximum number of related products to return', type=int, default=4)
    def get(self, product_id):
        """Get related products"""
        product = Product.get_by_id(product_id)

        if not product:
            products_ns.abort(404, 'Product not found')

        limit = request.args.get('limit', 4, type=int)

        # Get related products
        related_products = product.get_related_products(limit=limit)

        # If no manually set related products, suggest products from same category
        if not related_products:
            related_products = Product.get_by_category(
                product.category_id,
                limit=limit + 1  # +1 to exclude self
            )
            # Exclude the current product
            related_products = [p for p in related_products if p.id != product.id][:limit]

        related_products_dict = [p.to_dict() for p in related_products]

        return {
            'products': related_products_dict,
            'pagination': {
                'page': 1,
                'per_page': len(related_products_dict),
                'total': len(related_products_dict),
                'total_pages': 1,
                'has_next': False,
                'has_prev': False
            },
            'search': None,
            'sort': None
        }, 200

    @products_ns.doc('update_related_products',
                     description='Admin endpoint to manage related products. Requires admin role.',
                     security='Bearer Auth')
    @jwt_required
    @admin_required
    @products_ns.expect(related_products_model, validate=True)
    @products_ns.marshal_with(product_model)
    def put(self, product_id):
        """Update related products (admin only)"""
        product = Product.get_by_id(product_id)

        if not product:
            products_ns.abort(404, 'Product not found')

        data = request.json
        product_ids = data.get('product_ids', [])

        # Validate product IDs
        if not isinstance(product_ids, list):
            products_ns.abort(400, 'product_ids must be a list')

        # Set related products (method handles validation)
        product.set_related_products(product_ids)
        product.save()

        return product.to_dict(include_related=True), 200