from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from google.cloud.firestore_v1.base_query import FieldFilter
from app.services.firebase_service import get_db


class Payment:
    """
    Represents a payment transaction in the e-commerce system.
    Supports multiple payment gateways (Stripe, PayPal, etc.) and tracks
    the complete payment lifecycle.
    """

    # Payment status constants
    STATUS_PENDING = 'pending'          # Payment initiated, awaiting completion
    STATUS_PROCESSING = 'processing'    # Payment being processed by gateway
    STATUS_COMPLETED = 'completed'      # Payment successful
    STATUS_FAILED = 'failed'            # Payment failed
    STATUS_CANCELLED = 'cancelled'      # Payment cancelled by user
    STATUS_REFUNDED = 'refunded'        # Payment refunded
    STATUS_PARTIALLY_REFUNDED = 'partially_refunded'  # Partial refund issued

    # Payment method constants
    METHOD_CREDIT_CARD = 'credit_card'
    METHOD_DEBIT_CARD = 'debit_card'
    METHOD_PAYPAL = 'paypal'
    METHOD_STRIPE = 'stripe'
    METHOD_BANK_TRANSFER = 'bank_transfer'
    METHOD_CASH_ON_DELIVERY = 'cash_on_delivery'
    METHOD_OTHER = 'other'

    # Payment gateway constants
    GATEWAY_STRIPE = 'stripe'
    GATEWAY_PAYPAL = 'paypal'
    GATEWAY_MANUAL = 'manual'
    GATEWAY_OTHER = 'other'

    def __init__(self, order_id: str, amount: float, payment_id: Optional[str] = None,
                 payment_method: str = METHOD_CREDIT_CARD, gateway: str = GATEWAY_STRIPE):
        self.id = payment_id
        self.order_id = order_id
        self.user_id = None  # Will be set from order

        # Payment details
        self.amount = amount
        self.currency = 'USD'  # Default currency
        self.payment_method = payment_method
        self.gateway = gateway
        self.status = self.STATUS_PENDING

        # Gateway-specific information
        self.gateway_transaction_id = None  # Transaction ID from payment gateway
        self.gateway_payment_intent_id = None  # Payment intent ID (Stripe)
        self.gateway_response = {}  # Full response from gateway (for debugging)

        # Card information (last 4 digits only for security)
        self.card_last_four = None
        self.card_brand = None  # visa, mastercard, amex, etc.
        self.card_exp_month = None
        self.card_exp_year = None

        # Refund tracking
        self.refund_amount = 0.0
        self.refund_reason = None
        self.refunded_at = None

        # Payment metadata
        self.description = None
        self.customer_email = None
        self.customer_name = None

        # Error tracking
        self.error_code = None
        self.error_message = None

        # Timestamps
        self.created_at = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)
        self.completed_at = None
        self.failed_at = None
        self.cancelled_at = None

    def to_dict(self, include_sensitive: bool = False) -> Dict[str, Any]:
        """Convert Payment to dictionary for Firestore storage"""
        data = {
            'id': self.id,
            'order_id': self.order_id,
            'user_id': self.user_id,
            'amount': self.amount,
            'currency': self.currency,
            'payment_method': self.payment_method,
            'gateway': self.gateway,
            'status': self.status,
            'gateway_transaction_id': self.gateway_transaction_id,
            'gateway_payment_intent_id': self.gateway_payment_intent_id,
            'card_last_four': self.card_last_four,
            'card_brand': self.card_brand,
            'card_exp_month': self.card_exp_month,
            'card_exp_year': self.card_exp_year,
            'refund_amount': self.refund_amount,
            'refund_reason': self.refund_reason,
            'refunded_at': self.refunded_at.isoformat() if self.refunded_at else None,
            'description': self.description,
            'customer_email': self.customer_email,
            'customer_name': self.customer_name,
            'error_code': self.error_code,
            'error_message': self.error_message,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'failed_at': self.failed_at.isoformat() if self.failed_at else None,
            'cancelled_at': self.cancelled_at.isoformat() if self.cancelled_at else None
        }

        # Include gateway response only if sensitive data is requested (for admin/debugging)
        if include_sensitive:
            data['gateway_response'] = self.gateway_response

        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any], payment_id: str = None) -> 'Payment':
        """Create Payment from dictionary"""
        payment = cls(
            order_id=data['order_id'],
            amount=data['amount'],
            payment_id=payment_id,
            payment_method=data.get('payment_method', cls.METHOD_CREDIT_CARD),
            gateway=data.get('gateway', cls.GATEWAY_STRIPE)
        )

        # Restore basic fields
        payment.user_id = data.get('user_id')
        payment.currency = data.get('currency', 'USD')
        payment.status = data.get('status', cls.STATUS_PENDING)

        # Restore gateway information
        payment.gateway_transaction_id = data.get('gateway_transaction_id')
        payment.gateway_payment_intent_id = data.get('gateway_payment_intent_id')
        payment.gateway_response = data.get('gateway_response', {})

        # Restore card information
        payment.card_last_four = data.get('card_last_four')
        payment.card_brand = data.get('card_brand')
        payment.card_exp_month = data.get('card_exp_month')
        payment.card_exp_year = data.get('card_exp_year')

        # Restore refund information
        payment.refund_amount = data.get('refund_amount', 0.0)
        payment.refund_reason = data.get('refund_reason')
        if data.get('refunded_at'):
            payment.refunded_at = datetime.fromisoformat(data['refunded_at'])

        # Restore metadata
        payment.description = data.get('description')
        payment.customer_email = data.get('customer_email')
        payment.customer_name = data.get('customer_name')

        # Restore error information
        payment.error_code = data.get('error_code')
        payment.error_message = data.get('error_message')

        # Restore timestamps
        if 'created_at' in data:
            payment.created_at = datetime.fromisoformat(data['created_at'])
        if 'updated_at' in data:
            payment.updated_at = datetime.fromisoformat(data['updated_at'])
        if data.get('completed_at'):
            payment.completed_at = datetime.fromisoformat(data['completed_at'])
        if data.get('failed_at'):
            payment.failed_at = datetime.fromisoformat(data['failed_at'])
        if data.get('cancelled_at'):
            payment.cancelled_at = datetime.fromisoformat(data['cancelled_at'])

        return payment

    def save(self) -> str:
        """Save payment to Firestore"""
        db = get_db()
        self.updated_at = datetime.now(timezone.utc)
        data = self.to_dict(include_sensitive=True)
        data.pop('id', None)

        if self.id:
            db.collection('payments').document(self.id).set(data)
            return self.id
        else:
            doc_ref = db.collection('payments').add(data)[1]
            self.id = doc_ref.id
            return self.id

    @classmethod
    def get_by_id(cls, payment_id: str) -> Optional['Payment']:
        """Get payment by ID"""
        db = get_db()
        doc = db.collection('payments').document(payment_id).get()

        if doc.exists:
            return cls.from_dict(doc.to_dict(), payment_id)
        return None

    @classmethod
    def get_by_order_id(cls, order_id: str) -> List['Payment']:
        """Get all payments for an order"""
        db = get_db()
        docs = db.collection('payments')\
            .where(filter=FieldFilter('order_id', '==', order_id))\
            .stream()

        payments = [cls.from_dict(doc.to_dict(), doc.id) for doc in docs]

        # Sort by created_at descending (newest first)
        payments.sort(key=lambda p: p.created_at, reverse=True)

        return payments

    @classmethod
    def get_by_user_id(cls, user_id: str, limit: Optional[int] = None) -> List['Payment']:
        """Get all payments for a user"""
        db = get_db()
        query = db.collection('payments').where(filter=FieldFilter('user_id', '==', user_id))

        docs = query.stream()
        payments = [cls.from_dict(doc.to_dict(), doc.id) for doc in docs]

        # Sort by created_at descending (newest first)
        payments.sort(key=lambda p: p.created_at, reverse=True)

        if limit:
            payments = payments[:limit]

        return payments

    @classmethod
    def get_by_gateway_transaction_id(cls, gateway_transaction_id: str) -> Optional['Payment']:
        """Get payment by gateway transaction ID"""
        db = get_db()
        docs = db.collection('payments')\
            .where(filter=FieldFilter('gateway_transaction_id', '==', gateway_transaction_id))\
            .limit(1)\
            .stream()

        for doc in docs:
            return cls.from_dict(doc.to_dict(), doc.id)
        return None

    def delete(self) -> bool:
        """
        Delete payment from Firestore.
        WARNING: Use with extreme caution. Payments should rarely be deleted.
        Consider marking as cancelled instead.
        """
        if not self.id:
            return False

        db = get_db()
        db.collection('payments').document(self.id).delete()
        return True

    # Payment Status Management

    def mark_as_processing(self, gateway_transaction_id: Optional[str] = None) -> None:
        """Mark payment as processing"""
        self.status = self.STATUS_PROCESSING
        if gateway_transaction_id:
            self.gateway_transaction_id = gateway_transaction_id
        self.updated_at = datetime.now(timezone.utc)

    def mark_as_completed(self, gateway_transaction_id: Optional[str] = None) -> None:
        """Mark payment as completed"""
        self.status = self.STATUS_COMPLETED
        if gateway_transaction_id:
            self.gateway_transaction_id = gateway_transaction_id
        self.completed_at = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)

    def mark_as_failed(self, error_code: Optional[str] = None,
                       error_message: Optional[str] = None) -> None:
        """Mark payment as failed"""
        self.status = self.STATUS_FAILED
        self.error_code = error_code
        self.error_message = error_message
        self.failed_at = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)

    def mark_as_cancelled(self) -> None:
        """Mark payment as cancelled"""
        self.status = self.STATUS_CANCELLED
        self.cancelled_at = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)

    def mark_as_refunded(self, refund_amount: float, reason: Optional[str] = None) -> None:
        """Mark payment as refunded (full or partial)"""
        self.refund_amount += refund_amount
        self.refund_reason = reason
        self.refunded_at = datetime.now(timezone.utc)

        # Determine if fully or partially refunded
        if self.refund_amount >= self.amount:
            self.status = self.STATUS_REFUNDED
        else:
            self.status = self.STATUS_PARTIALLY_REFUNDED

        self.updated_at = datetime.now(timezone.utc)

    # Payment Validation

    def validate(self) -> List[str]:
        """
        Validate payment fields and return list of validation errors.
        Returns empty list if validation passes.
        """
        errors = []

        if not self.order_id:
            errors.append("Order ID is required")

        if self.amount is None or self.amount <= 0:
            errors.append("Amount must be greater than 0")

        if not self.currency:
            errors.append("Currency is required")

        valid_methods = [
            self.METHOD_CREDIT_CARD, self.METHOD_DEBIT_CARD, self.METHOD_PAYPAL,
            self.METHOD_STRIPE, self.METHOD_BANK_TRANSFER, self.METHOD_CASH_ON_DELIVERY,
            self.METHOD_OTHER
        ]
        if self.payment_method not in valid_methods:
            errors.append(f"Invalid payment method. Must be one of: {', '.join(valid_methods)}")

        valid_gateways = [self.GATEWAY_STRIPE, self.GATEWAY_PAYPAL, self.GATEWAY_MANUAL, self.GATEWAY_OTHER]
        if self.gateway not in valid_gateways:
            errors.append(f"Invalid gateway. Must be one of: {', '.join(valid_gateways)}")

        valid_statuses = [
            self.STATUS_PENDING, self.STATUS_PROCESSING, self.STATUS_COMPLETED,
            self.STATUS_FAILED, self.STATUS_CANCELLED, self.STATUS_REFUNDED,
            self.STATUS_PARTIALLY_REFUNDED
        ]
        if self.status not in valid_statuses:
            errors.append(f"Invalid status. Must be one of: {', '.join(valid_statuses)}")

        if self.refund_amount < 0:
            errors.append("Refund amount cannot be negative")

        if self.refund_amount > self.amount:
            errors.append("Refund amount cannot exceed payment amount")

        return errors

    def is_valid(self) -> bool:
        """Check if payment is valid"""
        return len(self.validate()) == 0

    # Payment Queries

    def is_successful(self) -> bool:
        """Check if payment was successful"""
        return self.status == self.STATUS_COMPLETED

    def is_pending(self) -> bool:
        """Check if payment is pending"""
        return self.status == self.STATUS_PENDING

    def is_failed(self) -> bool:
        """Check if payment failed"""
        return self.status == self.STATUS_FAILED

    def can_be_refunded(self) -> bool:
        """Check if payment can be refunded"""
        return (self.status in [self.STATUS_COMPLETED, self.STATUS_PARTIALLY_REFUNDED] and
                self.refund_amount < self.amount)

    def get_remaining_refundable_amount(self) -> float:
        """Get the amount that can still be refunded"""
        if self.status not in [self.STATUS_COMPLETED, self.STATUS_PARTIALLY_REFUNDED]:
            return 0.0
        return self.amount - self.refund_amount

    # Helper Methods

    def set_card_info(self, last_four: str, brand: str,
                      exp_month: int = None, exp_year: int = None) -> None:
        """Set card information (only last 4 digits for security)"""
        self.card_last_four = last_four
        self.card_brand = brand.lower()
        self.card_exp_month = exp_month
        self.card_exp_year = exp_year

    def get_masked_card_number(self) -> Optional[str]:
        """Get masked card number for display (e.g., '**** **** **** 1234')"""
        if not self.card_last_four:
            return None
        return f"**** **** **** {self.card_last_four}"

    def get_payment_summary(self) -> str:
        """Get a human-readable payment summary"""
        summary_parts = []

        if self.payment_method:
            summary_parts.append(self.payment_method.replace('_', ' ').title())

        if self.card_last_four:
            summary_parts.append(f"ending in {self.card_last_four}")

        if self.amount:
            summary_parts.append(f"${self.amount:.2f} {self.currency}")

        if self.status:
            summary_parts.append(f"({self.status})")

        return " - ".join(summary_parts) if summary_parts else "Payment"

    @classmethod
    def get_total_by_user(cls, user_id: str, status: Optional[str] = None) -> float:
        """Get total amount paid by user, optionally filtered by status"""
        payments = cls.get_by_user_id(user_id)

        total = 0.0
        for payment in payments:
            if status is None or payment.status == status:
                total += payment.amount

        return total
