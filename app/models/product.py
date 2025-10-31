from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from app.services.firebase_service import get_db


class Product:
    def __init__(self, name: str, description: str, media: List[Dict[str, str]],
                 price: float, track_quantity: bool, weight: Optional[float],
                 size: Optional[str], variants: List[Dict[str, Any]], category_id: str,
                 stock: int, requires_selling_stock: bool, product_id: Optional[str] = None,
                 related_product_ids: Optional[List[str]] = None):
        self.id = product_id
        self.name = name
        self.description = description
        self.media = media or []
        self.price = price
        self.track_quantity = track_quantity
        self.weight = weight
        self.size = size
        self.variants = variants or []
        self.category_id = category_id
        self.created_at = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)
        self.stock = stock
        self.requires_selling_stock = requires_selling_stock
        self.related_product_ids = related_product_ids or []

    def to_dict(self, include_category: bool = False, include_related: bool = False) -> Dict[str, Any]:
        data = {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'media': self.media,
            'price': self.price,
            'track_quantity': self.track_quantity,
            'weight': self.weight,
            'size': self.size,
            'variants': self.variants,
            'category_id': self.category_id,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'stock': self.stock,
            'requires_selling_stock': self.requires_selling_stock,
            'related_product_ids': self.related_product_ids
        }

        if include_category and self.category_id:
            from app.models.category import Category
            category = Category.get_by_id(self.category_id)
            data['category'] = category.to_dict() if category else None

        if include_related and self.related_product_ids:
            related_products = self.get_related_products()
            data['related_products'] = [p.to_dict() for p in related_products]

        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any], product_id: str = None):
        product = cls(
            name=data['name'],
            description=data['description'],
            media=data.get('media', []),
            price=data['price'],
            track_quantity=data.get('track_quantity', True),
            weight=data.get('weight'),
            size=data.get('size'),
            variants=data.get('variants', []),
            category_id=data.get('category_id') or data.get('category'),  # Support both old and new format
            stock=data.get('stock', 0),
            requires_selling_stock=data.get('requires_selling_stock', False),
            product_id=product_id,
            related_product_ids=data.get('related_product_ids', [])
        )

        if 'created_at' in data:
            product.created_at = datetime.fromisoformat(data['created_at'])
        if 'updated_at' in data:
            product.updated_at = datetime.fromisoformat(data['updated_at'])

        return product

    def save(self) -> str:
        db = get_db()
        data = self.to_dict()
        data.pop('id', None)

        if self.id:
            db.collection('products').document(self.id).set(data)
            return self.id
        else:
            doc_ref = db.collection('products').add(data)[1]
            self.id = doc_ref.id
            return self.id

    @classmethod
    def get_by_id(cls, product_id: str) -> Optional['Product']:
        db = get_db()
        doc = db.collection('products').document(product_id).get()

        if doc.exists:
            return cls.from_dict(doc.to_dict(), product_id)
        return None

    @classmethod
    def get_all(cls, limit: Optional[int] = None, offset: Optional[int] = None, 
                search: Optional[str] = None, sort_by: Optional[str] = None, 
                sort_order: str = 'asc', category_id: Optional[str] = None) -> list['Product']:
        db = get_db()
        query = db.collection('products')
        
        docs = query.stream()
        products = [cls.from_dict(doc.to_dict(), doc.id) for doc in docs]
        
        # Filter by category if specified
        if category_id:
            products = [product for product in products if product.category_id == category_id]
        
        # Search functionality with category name lookup
        if search:
            search_lower = search.lower()
            from app.models.category import Category
            filtered_products = []
            
            for product in products:
                # Search in product name and description
                if (search_lower in product.name.lower() or 
                    search_lower in product.description.lower()):
                    filtered_products.append(product)
                    continue
                
                # Search in category name
                if product.category_id:
                    category = Category.get_by_id(product.category_id)
                    if category and search_lower in category.name.lower():
                        filtered_products.append(product)
            
            products = filtered_products
        
        # Sorting with category support
        if sort_by:
            reverse_order = sort_order.lower() == 'desc'
            if sort_by == 'created_at':
                products.sort(key=lambda p: p.created_at, reverse=reverse_order)
            elif sort_by == 'name':
                products.sort(key=lambda p: p.name.lower(), reverse=reverse_order)
            elif sort_by == 'price':
                products.sort(key=lambda p: p.price, reverse=reverse_order)
            elif sort_by == 'category':
                from app.models.category import Category
                def get_category_name(product):
                    if product.category_id:
                        category = Category.get_by_id(product.category_id)
                        return category.name.lower() if category else ''
                    return ''
                products.sort(key=get_category_name, reverse=reverse_order)
        
        if offset:
            products = products[offset:]
        if limit:
            products = products[:limit]
            
        return products
    
    @classmethod
    def count(cls, search: Optional[str] = None, category_id: Optional[str] = None) -> int:
        db = get_db()
        docs = db.collection('products').stream()
        products = [cls.from_dict(doc.to_dict(), doc.id) for doc in docs]
        
        # Filter by category if specified
        if category_id:
            products = [product for product in products if product.category_id == category_id]
        
        # Apply search filter
        if search:
            search_lower = search.lower()
            from app.models.category import Category
            filtered_products = []
            
            for product in products:
                # Search in product name and description
                if (search_lower in product.name.lower() or 
                    search_lower in product.description.lower()):
                    filtered_products.append(product)
                    continue
                
                # Search in category name
                if product.category_id:
                    category = Category.get_by_id(product.category_id)
                    if category and search_lower in category.name.lower():
                        filtered_products.append(product)
            
            products = filtered_products
        
        return len(products)

    @classmethod
    def get_by_category(cls, category_id: str, limit: Optional[int] = None, offset: Optional[int] = None) -> list['Product']:
        """Get products by category ID"""
        return cls.get_all(limit=limit, offset=offset, category_id=category_id)

    def validate_category(self) -> bool:
        """Validate that the product's category exists"""
        if not self.category_id:
            return False

        from app.models.category import Category
        category = Category.get_by_id(self.category_id)
        return category is not None and category.is_active

    # Related Products Management

    def get_related_products(self, limit: Optional[int] = None) -> List['Product']:
        """Get related products for this product"""
        if not self.related_product_ids:
            return []

        related_products = []
        for product_id in self.related_product_ids:
            product = Product.get_by_id(product_id)
            if product:  # Only include products that still exist
                related_products.append(product)

        if limit:
            related_products = related_products[:limit]

        return related_products

    def add_related_product(self, product_id: str) -> bool:
        """Add a product to the related products list"""
        if not product_id or product_id == self.id:
            return False  # Can't relate to itself

        if product_id in self.related_product_ids:
            return False  # Already related

        # Verify product exists
        if not Product.get_by_id(product_id):
            return False

        self.related_product_ids.append(product_id)
        self.updated_at = datetime.now(timezone.utc)
        return True

    def remove_related_product(self, product_id: str) -> bool:
        """Remove a product from the related products list"""
        if product_id in self.related_product_ids:
            self.related_product_ids.remove(product_id)
            self.updated_at = datetime.now(timezone.utc)
            return True
        return False

    def set_related_products(self, product_ids: List[str]) -> bool:
        """Set the complete list of related products"""
        # Filter out invalid IDs (self, non-existent products)
        valid_ids = []
        for pid in product_ids:
            if pid and pid != self.id and Product.get_by_id(pid):
                valid_ids.append(pid)

        self.related_product_ids = valid_ids
        self.updated_at = datetime.now(timezone.utc)
        return True

    def delete(self) -> bool:
        if not self.id:
            return False

        db = get_db()
        db.collection('products').document(self.id).delete()
        return True