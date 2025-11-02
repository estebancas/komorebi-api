from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from app.services.firebase_service import get_db


class InventoryTransaction:
    """
    Tracks all stock changes for products that require inventory management.

    This provides an audit trail of stock movements, helping track:
    - When stock levels changed
    - Why they changed (sale, restock, adjustment, return)
    - Who made the change
    - Reference to related entities (orders, etc.)
    """

    TRANSACTION_TYPES = [
        'sale',          # Stock reduced due to order
        'restock',       # Stock added (purchase/production)
        'adjustment',    # Manual correction (damage, loss, found)
        'return',        # Stock returned from customer
        'reservation',   # Stock reserved for pending order
        'release'        # Reserved stock released back
    ]

    def __init__(self, product_id: str, quantity: int, transaction_type: str,
                 reference_id: Optional[str] = None, notes: Optional[str] = None,
                 created_by: Optional[str] = None, transaction_id: Optional[str] = None):
        """
        Args:
            product_id: ID of the product
            quantity: Change in quantity (positive for additions, negative for reductions)
            transaction_type: Type of transaction (sale, restock, adjustment, return, etc.)
            reference_id: Reference to related entity (order_id, etc.)
            notes: Additional notes about the transaction
            created_by: User ID who created the transaction
            transaction_id: Optional existing transaction ID
        """
        self.id = transaction_id
        self.product_id = product_id
        self.quantity = quantity
        self.transaction_type = transaction_type
        self.reference_id = reference_id
        self.notes = notes
        self.created_by = created_by
        self.created_at = datetime.now(timezone.utc)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'product_id': self.product_id,
            'quantity': self.quantity,
            'transaction_type': self.transaction_type,
            'reference_id': self.reference_id,
            'notes': self.notes,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat()
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any], transaction_id: str = None):
        transaction = cls(
            product_id=data['product_id'],
            quantity=data['quantity'],
            transaction_type=data['transaction_type'],
            reference_id=data.get('reference_id'),
            notes=data.get('notes'),
            created_by=data.get('created_by'),
            transaction_id=transaction_id
        )

        if 'created_at' in data:
            transaction.created_at = datetime.fromisoformat(data['created_at'])

        return transaction

    def save(self) -> str:
        """Save transaction to Firestore"""
        db = get_db()
        data = self.to_dict()
        data.pop('id', None)

        if self.id:
            db.collection('inventory_transactions').document(self.id).set(data)
            return self.id
        else:
            doc_ref = db.collection('inventory_transactions').add(data)[1]
            self.id = doc_ref.id
            return self.id

    @classmethod
    def get_by_id(cls, transaction_id: str) -> Optional['InventoryTransaction']:
        """Get transaction by ID"""
        db = get_db()
        doc = db.collection('inventory_transactions').document(transaction_id).get()

        if doc.exists:
            return cls.from_dict(doc.to_dict(), transaction_id)
        return None

    @classmethod
    def get_by_product(cls, product_id: str, limit: Optional[int] = None) -> List['InventoryTransaction']:
        """Get all transactions for a specific product, ordered by date descending"""
        db = get_db()
        query = db.collection('inventory_transactions').where('product_id', '==', product_id)

        docs = query.stream()
        transactions = [cls.from_dict(doc.to_dict(), doc.id) for doc in docs]

        # Sort by created_at descending (newest first)
        transactions.sort(key=lambda t: t.created_at, reverse=True)

        if limit:
            transactions = transactions[:limit]

        return transactions

    @classmethod
    def get_by_reference(cls, reference_id: str) -> List['InventoryTransaction']:
        """Get all transactions for a specific reference (e.g., order_id)"""
        db = get_db()
        query = db.collection('inventory_transactions').where('reference_id', '==', reference_id)

        docs = query.stream()
        transactions = [cls.from_dict(doc.to_dict(), doc.id) for doc in docs]

        # Sort by created_at descending (newest first)
        transactions.sort(key=lambda t: t.created_at, reverse=True)

        return transactions

    @classmethod
    def get_all(cls, limit: Optional[int] = None, transaction_type: Optional[str] = None) -> List['InventoryTransaction']:
        """Get all transactions, optionally filtered by type"""
        db = get_db()
        query = db.collection('inventory_transactions')

        if transaction_type:
            query = query.where('transaction_type', '==', transaction_type)

        docs = query.stream()
        transactions = [cls.from_dict(doc.to_dict(), doc.id) for doc in docs]

        # Sort by created_at descending (newest first)
        transactions.sort(key=lambda t: t.created_at, reverse=True)

        if limit:
            transactions = transactions[:limit]

        return transactions

    @classmethod
    def create_sale_transaction(cls, product_id: str, quantity: int, order_id: str,
                                created_by: Optional[str] = None) -> 'InventoryTransaction':
        """Helper to create a sale transaction"""
        transaction = cls(
            product_id=product_id,
            quantity=-abs(quantity),  # Always negative for sales
            transaction_type='sale',
            reference_id=order_id,
            notes=f'Stock reduced for order {order_id}',
            created_by=created_by
        )
        transaction.save()
        return transaction

    @classmethod
    def create_restock_transaction(cls, product_id: str, quantity: int,
                                   notes: Optional[str] = None,
                                   created_by: Optional[str] = None) -> 'InventoryTransaction':
        """Helper to create a restock transaction"""
        transaction = cls(
            product_id=product_id,
            quantity=abs(quantity),  # Always positive for restocks
            transaction_type='restock',
            notes=notes or 'Stock replenished',
            created_by=created_by
        )
        transaction.save()
        return transaction

    @classmethod
    def create_adjustment_transaction(cls, product_id: str, quantity: int,
                                      reason: str, created_by: Optional[str] = None) -> 'InventoryTransaction':
        """Helper to create an adjustment transaction"""
        transaction = cls(
            product_id=product_id,
            quantity=quantity,
            transaction_type='adjustment',
            notes=f'Inventory adjustment: {reason}',
            created_by=created_by
        )
        transaction.save()
        return transaction
