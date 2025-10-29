from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any, List
from app.services.firebase_service import get_db
from app.models.cart_item import CartItem


class Cart:
    """
    Represents a shopping cart for a user or guest.
    """
    # Cart status constants
    STATUS_ACTIVE = 'active'
    STATUS_CHECKED_OUT = 'checked_out'
    STATUS_EXPIRED = 'expired'
    STATUS_ABANDONED = 'abandoned'

    def __init__(self, user_id: Optional[str] = None, cart_id: Optional[str] = None,
                 status: str = STATUS_ACTIVE):
        self.id = cart_id
        self.user_id = user_id  # None for guest carts
        self.items: List[CartItem] = []
        self.status = status
        self.created_at = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)

        # Guest carts expire after 7 days by default
        if user_id is None:
            self.expires_at = datetime.now(timezone.utc) + timedelta(days=7)
        else:
            self.expires_at = None

    def to_dict(self, include_items_detail: bool = True) -> Dict[str, Any]:
        """Convert Cart to dictionary for Firestore storage"""
        data = {
            'id': self.id,
            'user_id': self.user_id,
            'status': self.status,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'expires_at': self.expires_at.isoformat() if self.expires_at else None
        }

        if include_items_detail:
            data['items'] = [item.to_dict() for item in self.items]
            data['item_count'] = len(self.items)
            data['total_quantity'] = sum(item.quantity for item in self.items)
            data['subtotal'] = self.get_subtotal()

        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any], cart_id: str = None) -> 'Cart':
        """Create Cart from dictionary"""
        cart = cls(
            user_id=data.get('user_id'),
            cart_id=cart_id,
            status=data.get('status', cls.STATUS_ACTIVE)
        )

        # Restore timestamps
        if 'created_at' in data:
            cart.created_at = datetime.fromisoformat(data['created_at'])
        if 'updated_at' in data:
            cart.updated_at = datetime.fromisoformat(data['updated_at'])
        if 'expires_at' in data and data['expires_at']:
            cart.expires_at = datetime.fromisoformat(data['expires_at'])

        # Restore cart items
        if 'items' in data:
            cart.items = [CartItem.from_dict(item_data) for item_data in data['items']]

        return cart

    def save(self) -> str:
        """Save cart to Firestore"""
        db = get_db()
        self.updated_at = datetime.now(timezone.utc)
        data = self.to_dict()
        data.pop('id', None)
        data.pop('item_count', None)
        data.pop('total_quantity', None)
        data.pop('subtotal', None)

        if self.id:
            db.collection('carts').document(self.id).set(data)
            return self.id
        else:
            doc_ref = db.collection('carts').add(data)[1]
            self.id = doc_ref.id
            return self.id

    @classmethod
    def get_by_id(cls, cart_id: str) -> Optional['Cart']:
        """Get cart by ID"""
        db = get_db()
        doc = db.collection('carts').document(cart_id).get()

        if doc.exists:
            return cls.from_dict(doc.to_dict(), cart_id)
        return None

    @classmethod
    def get_by_user_id(cls, user_id: str) -> Optional['Cart']:
        """Get active cart for a user"""
        db = get_db()
        docs = db.collection('carts')\
            .where('user_id', '==', user_id)\
            .where('status', '==', cls.STATUS_ACTIVE)\
            .limit(1)\
            .stream()

        for doc in docs:
            return cls.from_dict(doc.to_dict(), doc.id)
        return None

    @classmethod
    def get_or_create_for_user(cls, user_id: str) -> 'Cart':
        """Get existing active cart or create new one for user"""
        cart = cls.get_by_user_id(user_id)
        if cart:
            return cart

        # Create new cart for user
        cart = cls(user_id=user_id)
        cart.save()
        return cart

    def delete(self) -> bool:
        """Delete cart from Firestore"""
        if not self.id:
            return False

        db = get_db()
        db.collection('carts').document(self.id).delete()
        return True

    # Cart Item Management Methods

    def add_item(self, product_id: str, product_name: str, price: float,
                 quantity: int = 1, variant: Optional[Dict[str, Any]] = None) -> CartItem:
        """Add item to cart or update quantity if already exists"""
        # Check if item with same product and variant already exists
        existing_item = self.find_item(product_id, variant)

        if existing_item:
            existing_item.quantity += quantity
            return existing_item
        else:
            # Create new cart item
            new_item = CartItem(
                product_id=product_id,
                product_name=product_name,
                quantity=quantity,
                price_at_addition=price,
                variant=variant
            )
            self.items.append(new_item)
            return new_item

    def find_item(self, product_id: str, variant: Optional[Dict[str, Any]] = None) -> Optional[CartItem]:
        """Find cart item by product_id and variant"""
        for item in self.items:
            if item.matches_product(product_id, variant):
                return item
        return None

    def remove_item(self, item_id: str) -> bool:
        """Remove item from cart by item_id"""
        for i, item in enumerate(self.items):
            if item.id == item_id:
                self.items.pop(i)
                return True
        return False

    def update_item_quantity(self, item_id: str, new_quantity: int) -> bool:
        """Update quantity of a cart item"""
        for item in self.items:
            if item.id == item_id:
                if new_quantity < 1:
                    # Remove item if quantity is 0 or negative
                    return self.remove_item(item_id)
                item.update_quantity(new_quantity)
                return True
        return False

    def clear_items(self) -> None:
        """Remove all items from cart"""
        self.items = []

    # Cart Calculation Methods

    def get_subtotal(self) -> float:
        """Calculate subtotal of all items in cart"""
        return sum(item.get_subtotal() for item in self.items)

    def get_total_items(self) -> int:
        """Get total number of unique items in cart"""
        return len(self.items)

    def get_total_quantity(self) -> int:
        """Get total quantity of all items in cart"""
        return sum(item.quantity for item in self.items)

    def is_empty(self) -> bool:
        """Check if cart has no items"""
        return len(self.items) == 0

    # Cart Status Methods

    def is_expired(self) -> bool:
        """Check if cart has expired"""
        if self.expires_at:
            return datetime.now(timezone.utc) > self.expires_at
        return False

    def is_active(self) -> bool:
        """Check if cart is active and not expired"""
        return self.status == self.STATUS_ACTIVE and not self.is_expired()

    def mark_as_checked_out(self) -> None:
        """Mark cart as checked out (converted to order)"""
        self.status = self.STATUS_CHECKED_OUT
        self.updated_at = datetime.now(timezone.utc)

    def mark_as_expired(self) -> None:
        """Mark cart as expired"""
        self.status = self.STATUS_EXPIRED
        self.updated_at = datetime.now(timezone.utc)

    def mark_as_abandoned(self) -> None:
        """Mark cart as abandoned"""
        self.status = self.STATUS_ABANDONED
        self.updated_at = datetime.now(timezone.utc)

    # Validation Methods

    def validate_items_stock(self) -> List[Dict[str, Any]]:
        """
        Validate that all items in cart have sufficient stock.
        Returns list of items with stock issues.
        """
        from app.models.product import Product

        issues = []
        for item in self.items:
            product = Product.get_by_id(item.product_id)

            if not product:
                issues.append({
                    'item_id': item.id,
                    'product_id': item.product_id,
                    'issue': 'Product not found'
                })
                continue

            if product.track_quantity and product.requires_selling_stock:
                if product.stock < item.quantity:
                    issues.append({
                        'item_id': item.id,
                        'product_id': item.product_id,
                        'product_name': item.product_name,
                        'requested_quantity': item.quantity,
                        'available_stock': product.stock,
                        'issue': 'Insufficient stock'
                    })

        return issues
