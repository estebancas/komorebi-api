from datetime import datetime, timezone
from typing import Optional, Dict, Any


class OrderItem:
    """
    Represents a single item in an order.
    Order items are stored as part of the Order document, not as separate documents.
    This is a snapshot of the product at the time of purchase.
    """
    def __init__(self, product_id: str, product_name: str, quantity: int,
                 unit_price: float, variant: Optional[Dict[str, Any]] = None,
                 item_id: Optional[str] = None):
        self.id = item_id or f"{product_id}_{datetime.now(timezone.utc).timestamp()}"
        self.product_id = product_id
        self.product_name = product_name  # Product name at time of purchase
        self.quantity = quantity
        self.unit_price = unit_price  # Price per unit at time of purchase
        self.variant = variant or {}  # Product variant details (e.g., size, color, scent)

    def to_dict(self) -> Dict[str, Any]:
        """Convert OrderItem to dictionary for Firestore storage"""
        return {
            'id': self.id,
            'product_id': self.product_id,
            'product_name': self.product_name,
            'quantity': self.quantity,
            'unit_price': self.unit_price,
            'variant': self.variant,
            'total_price': self.get_total_price()
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'OrderItem':
        """Create OrderItem from dictionary"""
        return cls(
            product_id=data['product_id'],
            product_name=data['product_name'],
            quantity=data['quantity'],
            unit_price=data['unit_price'],
            variant=data.get('variant', {}),
            item_id=data.get('id')
        )

    def get_total_price(self) -> float:
        """Calculate total price for this order item (unit_price * quantity)"""
        return self.unit_price * self.quantity

    @classmethod
    def from_cart_item(cls, cart_item) -> 'OrderItem':
        """
        Create an OrderItem from a CartItem.
        This converts a cart item to a finalized order item.
        """
        return cls(
            product_id=cart_item.product_id,
            product_name=cart_item.product_name,
            quantity=cart_item.quantity,
            unit_price=cart_item.price_at_addition,
            variant=cart_item.variant
        )
