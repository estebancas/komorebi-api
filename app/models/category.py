from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from google.cloud.firestore_v1.base_query import FieldFilter
from app.services.firebase_service import get_db


class Category:
    def __init__(self, name: str, description: Optional[str] = None, 
                 parent_id: Optional[str] = None, slug: Optional[str] = None,
                 is_active: bool = True, category_id: Optional[str] = None):
        self.id = category_id
        self.name = name
        self.description = description
        self.parent_id = parent_id
        self.slug = slug or self._generate_slug(name)
        self.is_active = is_active
        self.created_at = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)

    def _generate_slug(self, name: str) -> str:
        """Generate URL-friendly slug from category name"""
        import re
        slug = name.lower().strip()
        slug = re.sub(r'[^\w\s-]', '', slug)
        slug = re.sub(r'[\s_-]+', '-', slug)
        return slug.strip('-')

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'parent_id': self.parent_id,
            'slug': self.slug,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any], category_id: str = None):
        category = cls(
            name=data['name'],
            description=data.get('description'),
            parent_id=data.get('parent_id'),
            slug=data.get('slug'),
            is_active=data.get('is_active', True),
            category_id=category_id
        )

        if 'created_at' in data:
            category.created_at = datetime.fromisoformat(data['created_at'])
        if 'updated_at' in data:
            category.updated_at = datetime.fromisoformat(data['updated_at'])

        return category

    def save(self) -> str:
        db = get_db()
        data = self.to_dict()
        data.pop('id', None)

        # Check for duplicate slug
        if not self.id:
            existing_slug = self._check_slug_exists(self.slug)
            if existing_slug:
                self.slug = f"{self.slug}-{int(datetime.now().timestamp())}"
                data['slug'] = self.slug

        if self.id:
            db.collection('categories').document(self.id).set(data)
            return self.id
        else:
            doc_ref = db.collection('categories').add(data)[1]
            self.id = doc_ref.id
            return self.id

    def _check_slug_exists(self, slug: str) -> bool:
        """Check if slug already exists"""
        db = get_db()
        existing = db.collection('categories').where(filter=FieldFilter('slug', '==', slug)).limit(1).get()
        return len(existing) > 0

    @classmethod
    def get_by_id(cls, category_id: str) -> Optional['Category']:
        db = get_db()
        doc = db.collection('categories').document(category_id).get()

        if doc.exists:
            return cls.from_dict(doc.to_dict(), category_id)
        return None

    @classmethod
    def get_by_slug(cls, slug: str) -> Optional['Category']:
        db = get_db()
        docs = db.collection('categories').where(filter=FieldFilter('slug', '==', slug)).limit(1).get()

        if docs:
            doc = docs[0]
            return cls.from_dict(doc.to_dict(), doc.id)
        return None

    @classmethod
    def get_all(cls, active_only: bool = True) -> List['Category']:
        db = get_db()
        query = db.collection('categories')
        
        # Get all documents and filter/sort in memory to avoid composite index
        docs = query.stream()
        categories = [cls.from_dict(doc.to_dict(), doc.id) for doc in docs]
        
        if active_only:
            categories = [cat for cat in categories if cat.is_active]
        
        # Sort by name in memory
        categories.sort(key=lambda x: x.name.lower())
        return categories

    @classmethod
    def get_by_parent(cls, parent_id: Optional[str] = None, active_only: bool = True) -> List['Category']:
        """Get categories by parent_id. None for root categories."""
        db = get_db()
        query = db.collection('categories')
        
        # Get all documents and filter in memory to avoid composite index
        docs = query.stream()
        categories = [cls.from_dict(doc.to_dict(), doc.id) for doc in docs]
        
        # Filter by parent_id
        if parent_id:
            categories = [cat for cat in categories if cat.parent_id == parent_id]
        else:
            categories = [cat for cat in categories if cat.parent_id is None]
        
        # Filter by active status
        if active_only:
            categories = [cat for cat in categories if cat.is_active]
        
        # Sort by name in memory
        categories.sort(key=lambda x: x.name.lower())
        return categories

    @classmethod
    def get_hierarchy(cls, active_only: bool = True) -> List[Dict[str, Any]]:
        """Get categories in hierarchical structure"""
        all_categories = cls.get_all(active_only)
        
        # Create a dict for quick lookup
        category_dict = {cat.id: cat for cat in all_categories}
        
        # Build hierarchy
        hierarchy = []
        
        for category in all_categories:
            if not category.parent_id:  # Root category
                cat_data = category.to_dict()
                cat_data['children'] = cls._get_children(category.id, category_dict)
                hierarchy.append(cat_data)
        
        return hierarchy

    @classmethod
    def _get_children(cls, parent_id: str, category_dict: Dict[str, 'Category']) -> List[Dict[str, Any]]:
        """Recursively get children categories"""
        children = []
        
        for cat_id, category in category_dict.items():
            if category.parent_id == parent_id:
                cat_data = category.to_dict()
                cat_data['children'] = cls._get_children(cat_id, category_dict)
                children.append(cat_data)
        
        return sorted(children, key=lambda x: x['name'])

    @classmethod
    def count(cls, active_only: bool = True) -> int:
        db = get_db()
        query = db.collection('categories')
        
        # Get all documents and filter in memory to avoid index issues
        docs = query.stream()
        categories = [cls.from_dict(doc.to_dict(), doc.id) for doc in docs]
        
        if active_only:
            categories = [cat for cat in categories if cat.is_active]
            
        return len(categories)

    def delete(self) -> bool:
        """Soft delete - mark as inactive"""
        if not self.id:
            return False

        self.is_active = False
        self.updated_at = datetime.now(timezone.utc)
        self.save()
        return True

    def hard_delete(self) -> bool:
        """Permanently delete category"""
        if not self.id:
            return False

        # Check if category has children
        children = self.get_by_parent(self.id)
        if children:
            raise ValueError("Cannot delete category with children. Delete children first.")

        # Check if category has products
        from app.models.product import Product
        db = get_db()
        products = db.collection('products').where(filter=FieldFilter('category', '==', self.name)).limit(1).get()
        if products:
            raise ValueError("Cannot delete category with associated products.")

        db = get_db()
        db.collection('categories').document(self.id).delete()
        return True

    @classmethod
    def validate_name(cls, name: str) -> bool:
        """Validate category name"""
        if not name or len(name.strip()) < 2:
            return False
        if len(name.strip()) > 100:
            return False
        return True