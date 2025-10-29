from flask import request
from flask_restx import Namespace, Resource, fields
from app.models.category import Category
from datetime import datetime, timezone

categories_ns = Namespace('categories', description='Category operations', path='/categories')

# Define models for request/response documentation
category_model = categories_ns.model('Category', {
    'id': fields.String(description='Category ID'),
    'name': fields.String(required=True, description='Category name'),
    'description': fields.String(description='Category description'),
    'parent_id': fields.String(description='Parent category ID'),
    'slug': fields.String(description='URL-friendly category slug'),
    'is_active': fields.Boolean(description='Whether category is active'),
    'created_at': fields.DateTime(description='Creation timestamp'),
    'updated_at': fields.DateTime(description='Last update timestamp')
})

category_create_model = categories_ns.model('CategoryCreate', {
    'name': fields.String(required=True, description='Category name', min_length=2, max_length=100),
    'description': fields.String(description='Category description'),
    'parent_id': fields.String(description='Parent category ID'),
    'slug': fields.String(description='Custom URL slug (auto-generated if not provided)'),
    'is_active': fields.Boolean(description='Whether category is active', default=True)
})

category_update_model = categories_ns.model('CategoryUpdate', {
    'name': fields.String(description='Category name', min_length=2, max_length=100),
    'description': fields.String(description='Category description'),
    'parent_id': fields.String(description='Parent category ID'),
    'slug': fields.String(description='URL-friendly category slug'),
    'is_active': fields.Boolean(description='Whether category is active')
})

category_hierarchy_model = categories_ns.model('CategoryHierarchy', {
    'id': fields.String(description='Category ID'),
    'name': fields.String(description='Category name'),
    'description': fields.String(description='Category description'),
    'parent_id': fields.String(description='Parent category ID'),
    'slug': fields.String(description='URL-friendly category slug'),
    'is_active': fields.Boolean(description='Whether category is active'),
    'created_at': fields.DateTime(description='Creation timestamp'),
    'updated_at': fields.DateTime(description='Last update timestamp'),
    'children': fields.List(fields.Raw, description='Child categories (recursive)')
})

categories_list_model = categories_ns.model('CategoriesList', {
    'categories': fields.List(fields.Nested(category_model), description='List of categories'),
    'count': fields.Integer(description='Number of categories')
})

categories_hierarchy_response = categories_ns.model('CategoriesHierarchy', {
    'categories': fields.List(fields.Nested(category_hierarchy_model), description='Hierarchical category structure'),
    'count': fields.Integer(description='Total number of categories')
})


@categories_ns.route('/')
class CategoryList(Resource):
    @categories_ns.doc('list_categories')
    @categories_ns.marshal_with(categories_list_model)
    @categories_ns.param('active_only', 'Show only active categories', type=bool, default=True)
    @categories_ns.param('parent_id', 'Filter by parent category ID (use "null" for root categories)')
    def get(self):
        """Get all categories"""
        try:
            active_only = request.args.get('active_only', 'true').lower() == 'true'
            parent_id = request.args.get('parent_id')
            
            # Handle "null" string for root categories
            if parent_id == 'null':
                parent_id = None
            
            if parent_id is not None:
                categories = Category.get_by_parent(parent_id, active_only)
            else:
                categories = Category.get_all(active_only)
            
            categories_dict = [category.to_dict() for category in categories]
            
            return {
                'categories': categories_dict,
                'count': len(categories_dict)
            }, 200
            
        except Exception as e:
            print(f"Categories GET error: {str(e)}")
            categories_ns.abort(500, f'Failed to retrieve categories: {str(e)}')

    @categories_ns.doc('create_category')
    @categories_ns.expect(category_create_model, validate=True)
    @categories_ns.marshal_with(category_model, code=201)
    def post(self):
        """Create a new category"""
        data = request.json
        
        if not data:
            categories_ns.abort(400, 'No data provided')
        
        # Validate category name
        if not Category.validate_name(data['name']):
            categories_ns.abort(400, 'Category name must be between 2 and 100 characters')
        
        # Check if parent category exists (if provided)
        if data.get('parent_id'):
            parent = Category.get_by_id(data['parent_id'])
            if not parent:
                categories_ns.abort(400, 'Parent category not found')
        
        try:
            category = Category(
                name=data['name'],
                description=data.get('description'),
                parent_id=data.get('parent_id'),
                slug=data.get('slug'),
                is_active=data.get('is_active', True)
            )
            
            category.save()
            return category.to_dict(), 201
            
        except Exception as e:
            print(f"Category CREATE error: {str(e)}")
            categories_ns.abort(500, f'Failed to create category: {str(e)}')


@categories_ns.route('/hierarchy')
class CategoryHierarchy(Resource):
    @categories_ns.doc('get_category_hierarchy')
    @categories_ns.marshal_with(categories_hierarchy_response)
    @categories_ns.param('active_only', 'Show only active categories', type=bool, default=True)
    def get(self):
        """Get categories in hierarchical structure"""
        try:
            active_only = request.args.get('active_only', 'true').lower() == 'true'
            hierarchy = Category.get_hierarchy(active_only)
            
            return {
                'categories': hierarchy,
                'count': Category.count(active_only)
            }, 200
            
        except Exception:
            categories_ns.abort(500, 'Failed to retrieve category hierarchy')


@categories_ns.route('/<string:category_id>')
@categories_ns.param('category_id', 'The category identifier')
class CategoryItem(Resource):
    @categories_ns.doc('get_category')
    @categories_ns.marshal_with(category_model)
    def get(self, category_id):
        """Get a category by ID"""
        try:
            category = Category.get_by_id(category_id)
            
            if not category:
                categories_ns.abort(404, 'Category not found')
            
            return category.to_dict(), 200
            
        except Exception:
            categories_ns.abort(500, 'Failed to retrieve category')

    @categories_ns.doc('update_category')
    @categories_ns.expect(category_update_model, validate=False)
    @categories_ns.marshal_with(category_model)
    def put(self, category_id):
        """Update a category"""
        try:
            category = Category.get_by_id(category_id)
            
            if not category:
                categories_ns.abort(404, 'Category not found')
            
            data = request.json
            if not data:
                categories_ns.abort(400, 'No data provided')
            
            # Update fields if provided
            if 'name' in data:
                if not Category.validate_name(data['name']):
                    categories_ns.abort(400, 'Category name must be between 2 and 100 characters')
                category.name = data['name']
                
            if 'description' in data:
                category.description = data['description']
                
            if 'parent_id' in data:
                parent_id = data['parent_id']
                if parent_id and parent_id == category.id:
                    categories_ns.abort(400, 'Category cannot be its own parent')
                if parent_id:
                    parent = Category.get_by_id(parent_id)
                    if not parent:
                        categories_ns.abort(400, 'Parent category not found')
                category.parent_id = parent_id
                
            if 'slug' in data:
                category.slug = data['slug']
                
            if 'is_active' in data:
                category.is_active = data['is_active']
            
            # Update timestamp
            category.updated_at = datetime.now(timezone.utc)
            
            category.save()
            return category.to_dict(), 200
            
        except Exception:
            categories_ns.abort(500, 'Failed to update category')

    @categories_ns.doc('delete_category')
    def delete(self, category_id):
        """Delete a category (soft delete - marks as inactive)"""
        try:
            category = Category.get_by_id(category_id)
            
            if not category:
                categories_ns.abort(404, 'Category not found')
            
            if category.delete():
                return {'message': 'Category deleted successfully'}, 200
            else:
                categories_ns.abort(500, 'Failed to delete category')
            
        except Exception:
            categories_ns.abort(500, 'Failed to delete category')


@categories_ns.route('/slug/<string:slug>')
@categories_ns.param('slug', 'The category slug')
class CategoryBySlug(Resource):
    @categories_ns.doc('get_category_by_slug')
    @categories_ns.marshal_with(category_model)
    def get(self, slug):
        """Get a category by slug"""
        try:
            category = Category.get_by_slug(slug)
            
            if not category:
                categories_ns.abort(404, 'Category not found')
            
            return category.to_dict(), 200
            
        except Exception:
            categories_ns.abort(500, 'Failed to retrieve category')


@categories_ns.route('/<string:category_id>/hard-delete')
@categories_ns.param('category_id', 'The category identifier')
class CategoryHardDelete(Resource):
    @categories_ns.doc('hard_delete_category')
    def delete(self, category_id):
        """Permanently delete a category (use with caution!)"""
        try:
            category = Category.get_by_id(category_id)
            
            if not category:
                categories_ns.abort(404, 'Category not found')
            
            try:
                if category.hard_delete():
                    return {'message': 'Category permanently deleted'}, 200
                else:
                    categories_ns.abort(500, 'Failed to permanently delete category')
            except ValueError as e:
                categories_ns.abort(400, str(e))
            
        except Exception:
            categories_ns.abort(500, 'Failed to delete category')