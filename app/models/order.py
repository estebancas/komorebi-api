from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
import random
import string
from google.cloud.firestore_v1.base_query import FieldFilter
from app.services.firebase_service import get_db
from app.models.order_item import OrderItem


class Order:
    """
    Represents a customer order in the e-commerce system.
    Orders are created from carts and track the entire order lifecycle.
    """
    # Order status constants
    STATUS_PENDING = 'pending'  # Order created, awaiting payment
    STATUS_PROCESSING = 'processing'  # Payment received, preparing order
    STATUS_SHIPPED = 'shipped'  # Order shipped to customer
    STATUS_DELIVERED = 'delivered'  # Order delivered successfully
    STATUS_CANCELLED = 'cancelled'  # Order cancelled by customer or admin
    STATUS_REFUNDED = 'refunded'  # Order refunded

    def __init__(self, user_id: str, order_id: Optional[str] = None,
                 order_number: Optional[str] = None, status: str = STATUS_PENDING):
        self.id = order_id
        self.order_number = order_number or self._generate_order_number()
        self.user_id = user_id
        self.items: List[OrderItem] = []
        self.status = status

        # Financial details
        self.subtotal = 0.0
        self.tax = 0.0
        self.shipping = 0.0
        self.discount = 0.0
        self.total = 0.0

        # Address information (to be expanded)
        self.shipping_address = {}
        self.billing_address = {}

        # Payment information (to be expanded)
        self.payment_method = None
        self.payment_status = None
        self.payment_id = None

        # Notes and tracking
        self.customer_notes = None
        self.admin_notes = None
        self.tracking_number = None

        # Timestamps
        self.created_at = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)
        self.paid_at = None
        self.shipped_at = None
        self.delivered_at = None
        self.cancelled_at = None

    @staticmethod
    def _generate_order_number() -> str:
        """Generate a unique human-readable order number (e.g., ORD-20251028-ABC123)"""
        date_str = datetime.now(timezone.utc).strftime('%Y%m%d')
        random_str = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        return f"ORD-{date_str}-{random_str}"

    def to_dict(self, include_items_detail: bool = True) -> Dict[str, Any]:
        """Convert Order to dictionary for Firestore storage"""
        data = {
            'id': self.id,
            'order_number': self.order_number,
            'user_id': self.user_id,
            'status': self.status,
            'subtotal': self.subtotal,
            'tax': self.tax,
            'shipping': self.shipping,
            'discount': self.discount,
            'total': self.total,
            'shipping_address': self.shipping_address,
            'billing_address': self.billing_address,
            'payment_method': self.payment_method,
            'payment_status': self.payment_status,
            'payment_id': self.payment_id,
            'customer_notes': self.customer_notes,
            'admin_notes': self.admin_notes,
            'tracking_number': self.tracking_number,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'paid_at': self.paid_at.isoformat() if self.paid_at else None,
            'shipped_at': self.shipped_at.isoformat() if self.shipped_at else None,
            'delivered_at': self.delivered_at.isoformat() if self.delivered_at else None,
            'cancelled_at': self.cancelled_at.isoformat() if self.cancelled_at else None
        }

        if include_items_detail:
            data['items'] = [item.to_dict() for item in self.items]
            data['item_count'] = len(self.items)
            data['total_quantity'] = sum(item.quantity for item in self.items)

        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any], order_id: str = None) -> 'Order':
        """Create Order from dictionary"""
        order = cls(
            user_id=data['user_id'],
            order_id=order_id,
            order_number=data.get('order_number'),
            status=data.get('status', cls.STATUS_PENDING)
        )

        # Restore financial details
        order.subtotal = data.get('subtotal', 0.0)
        order.tax = data.get('tax', 0.0)
        order.shipping = data.get('shipping', 0.0)
        order.discount = data.get('discount', 0.0)
        order.total = data.get('total', 0.0)

        # Restore addresses
        order.shipping_address = data.get('shipping_address', {})
        order.billing_address = data.get('billing_address', {})

        # Restore payment info
        order.payment_method = data.get('payment_method')
        order.payment_status = data.get('payment_status')
        order.payment_id = data.get('payment_id')

        # Restore notes and tracking
        order.customer_notes = data.get('customer_notes')
        order.admin_notes = data.get('admin_notes')
        order.tracking_number = data.get('tracking_number')

        # Restore timestamps
        if 'created_at' in data:
            order.created_at = datetime.fromisoformat(data['created_at'])
        if 'updated_at' in data:
            order.updated_at = datetime.fromisoformat(data['updated_at'])
        if data.get('paid_at'):
            order.paid_at = datetime.fromisoformat(data['paid_at'])
        if data.get('shipped_at'):
            order.shipped_at = datetime.fromisoformat(data['shipped_at'])
        if data.get('delivered_at'):
            order.delivered_at = datetime.fromisoformat(data['delivered_at'])
        if data.get('cancelled_at'):
            order.cancelled_at = datetime.fromisoformat(data['cancelled_at'])

        # Restore order items
        if 'items' in data:
            order.items = [OrderItem.from_dict(item_data) for item_data in data['items']]

        return order

    def save(self) -> str:
        """Save order to Firestore"""
        db = get_db()
        self.updated_at = datetime.now(timezone.utc)
        data = self.to_dict()
        data.pop('id', None)
        data.pop('item_count', None)
        data.pop('total_quantity', None)

        if self.id:
            db.collection('orders').document(self.id).set(data)
            return self.id
        else:
            doc_ref = db.collection('orders').add(data)[1]
            self.id = doc_ref.id
            return self.id

    @classmethod
    def get_by_id(cls, order_id: str) -> Optional['Order']:
        """Get order by ID"""
        db = get_db()
        doc = db.collection('orders').document(order_id).get()

        if doc.exists:
            return cls.from_dict(doc.to_dict(), order_id)
        return None

    @classmethod
    def get_by_order_number(cls, order_number: str) -> Optional['Order']:
        """Get order by order number"""
        db = get_db()
        docs = db.collection('orders')\
            .where(filter=FieldFilter('order_number', '==', order_number))\
            .limit(1)\
            .stream()

        for doc in docs:
            return cls.from_dict(doc.to_dict(), doc.id)
        return None

    @classmethod
    def get_by_user_id(cls, user_id: str, limit: Optional[int] = None,
                       offset: Optional[int] = None) -> List['Order']:
        """Get all orders for a user"""
        db = get_db()
        query = db.collection('orders').where(filter=FieldFilter('user_id', '==', user_id))

        docs = query.stream()
        orders = [cls.from_dict(doc.to_dict(), doc.id) for doc in docs]

        # Sort by created_at descending (newest first)
        orders.sort(key=lambda o: o.created_at, reverse=True)

        if offset:
            orders = orders[offset:]
        if limit:
            orders = orders[:limit]

        return orders

    @classmethod
    def get_all(cls, limit: Optional[int] = None, offset: Optional[int] = None,
                status: Optional[str] = None) -> List['Order']:
        """Get all orders with optional filtering"""
        db = get_db()
        query = db.collection('orders')

        if status:
            query = query.where(filter=FieldFilter('status', '==', status))

        docs = query.stream()
        orders = [cls.from_dict(doc.to_dict(), doc.id) for doc in docs]

        # Sort by created_at descending (newest first)
        orders.sort(key=lambda o: o.created_at, reverse=True)

        if offset:
            orders = orders[offset:]
        if limit:
            orders = orders[:limit]

        return orders

    @classmethod
    def count_by_user(cls, user_id: str) -> int:
        """Count total orders for a user"""
        db = get_db()
        docs = db.collection('orders').where(filter=FieldFilter('user_id', '==', user_id)).stream()
        return len(list(docs))

    def delete(self) -> bool:
        """Delete order from Firestore (use with caution, prefer cancellation)"""
        if not self.id:
            return False

        db = get_db()
        db.collection('orders').document(self.id).delete()
        return True

    # Order Item Management

    def add_item(self, order_item: OrderItem) -> None:
        """Add an item to the order"""
        self.items.append(order_item)
        self._recalculate_totals()

    def add_items_from_cart(self, cart) -> None:
        """Add all items from a cart to this order"""
        for cart_item in cart.items:
            order_item = OrderItem.from_cart_item(cart_item)
            self.items.append(order_item)
        self._recalculate_totals()

    def _recalculate_totals(self) -> None:
        """Recalculate order totals based on items"""
        self.subtotal = sum(item.get_total_price() for item in self.items)
        # For now, total = subtotal (tax and shipping to be added later)
        self.total = self.subtotal + self.tax + self.shipping - self.discount

    # Order Calculations

    def get_item_count(self) -> int:
        """Get number of unique items in order"""
        return len(self.items)

    def get_total_quantity(self) -> int:
        """Get total quantity of all items"""
        return sum(item.quantity for item in self.items)

    # Order Status Management

    def can_cancel(self) -> bool:
        """Check if order can be cancelled"""
        return self.status in [self.STATUS_PENDING, self.STATUS_PROCESSING]

    def mark_as_processing(self) -> None:
        """Mark order as processing"""
        self.status = self.STATUS_PROCESSING
        self.updated_at = datetime.now(timezone.utc)

    def mark_as_paid(self, payment_id: Optional[str] = None) -> None:
        """Mark order as paid"""
        self.payment_status = 'paid'
        self.payment_id = payment_id
        self.paid_at = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)

    def mark_as_shipped(self, tracking_number: Optional[str] = None) -> None:
        """Mark order as shipped"""
        self.status = self.STATUS_SHIPPED
        self.tracking_number = tracking_number
        self.shipped_at = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)

    def mark_as_delivered(self) -> None:
        """Mark order as delivered"""
        self.status = self.STATUS_DELIVERED
        self.delivered_at = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)

    def mark_as_cancelled(self, reason: Optional[str] = None) -> None:
        """Mark order as cancelled"""
        if not self.can_cancel():
            raise ValueError(f"Cannot cancel order with status: {self.status}")

        self.status = self.STATUS_CANCELLED
        self.cancelled_at = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)

        if reason:
            self.admin_notes = f"Cancellation reason: {reason}"

    def mark_as_refunded(self) -> None:
        """Mark order as refunded"""
        self.status = self.STATUS_REFUNDED
        self.updated_at = datetime.now(timezone.utc)

    # Stock Management

    def reduce_product_stock(self) -> List[Dict[str, Any]]:
        """
        Reduce stock for all products in the order.
        Returns list of items that couldn't be reduced (insufficient stock).
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

            if product.track_quantity:
                if product.stock < item.quantity:
                    issues.append({
                        'item_id': item.id,
                        'product_id': item.product_id,
                        'product_name': item.product_name,
                        'requested_quantity': item.quantity,
                        'available_stock': product.stock,
                        'issue': 'Insufficient stock'
                    })
                else:
                    # Reduce stock
                    product.stock -= item.quantity
                    product.save()

        return issues

    @classmethod
    def create_from_cart(cls, cart, user_id: str) -> 'Order':
        """
        Create a new order from a cart.
        This is the main method for converting a cart to an order during checkout.
        """
        order = cls(user_id=user_id)
        order.add_items_from_cart(cart)
        return order
