from datetime import datetime, timezone
from typing import Optional, Dict, Any


class CartItem:
    """
    Represents an item in a shopping cart.
    Cart items are stored as part of the Cart document, not as separate documents.
    """
    def __init__(self, product_id: str, product_name: str, quantity: int,
                 price_at_addition: float, variant: Optional[Dict[str, Any]] = None,
                 item_id: Optional[str] = None):
        self.id = item_id or f"{product_id}_{datetime.now(timezone.utc).timestamp()}"
        self.product_id = product_id
        self.product_name = product_name  # Snapshot for reference
        self.quantity = quantity
        self.price_at_addition = price_at_addition  # Store price at time of addition
        self.variant = variant or {}  # Product variant details (e.g., size, color)
        self.added_at = datetime.now(timezone.utc)

    def to_dict(self) -> Dict[str, Any]:
        """Convert CartItem to dictionary for Firestore storage"""
        return {
            'id': self.id,
            'product_id': self.product_id,
            'product_name': self.product_name,
            'quantity': self.quantity,
            'price_at_addition': self.price_at_addition,
            'variant': self.variant,
            'added_at': self.added_at.isoformat()
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CartItem':
        """Create CartItem from dictionary"""
        item = cls(
            product_id=data['product_id'],
            product_name=data['product_name'],
            quantity=data['quantity'],
            price_at_addition=data['price_at_addition'],
            variant=data.get('variant', {}),
            item_id=data.get('id')
        )

        if 'added_at' in data:
            item.added_at = datetime.fromisoformat(data['added_at'])

        return item

    def get_subtotal(self) -> float:
        """Calculate subtotal for this cart item"""
        return self.price_at_addition * self.quantity

    def validate_quantity(self, max_quantity: int = 999) -> bool:
        """Validate quantity is within acceptable range"""
        return 1 <= self.quantity <= max_quantity

    def update_quantity(self, new_quantity: int) -> None:
        """Update the quantity of this cart item"""
        if new_quantity < 1:
            raise ValueError("Quantity must be at least 1")
        self.quantity = new_quantity

    def matches_product(self, product_id: str, variant: Optional[Dict[str, Any]] = None) -> bool:
        """Check if this cart item matches a product and variant combination"""
        if self.product_id != product_id:
            return False

        # If no variant specified, match if this item has no variant
        if variant is None:
            return not self.variant or len(self.variant) == 0

        # Compare variant dictionaries
        return self.variant == variant
