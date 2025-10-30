from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from google.cloud.firestore_v1.base_query import FieldFilter
from app.services.firebase_service import get_db


class PaymentMethod:
    """
    Represents a saved payment method for a user.
    This allows users to save payment methods (credit cards, PayPal, etc.)
    for faster checkout in future orders.
    """

    # Payment method type constants
    TYPE_CREDIT_CARD = 'credit_card'
    TYPE_DEBIT_CARD = 'debit_card'
    TYPE_PAYPAL = 'paypal'
    TYPE_BANK_ACCOUNT = 'bank_account'
    TYPE_OTHER = 'other'

    # Gateway constants
    GATEWAY_STRIPE = 'stripe'
    GATEWAY_PAYPAL = 'paypal'
    GATEWAY_MANUAL = 'manual'

    def __init__(self, user_id: str, payment_method_id: Optional[str] = None,
                 method_type: str = TYPE_CREDIT_CARD, gateway: str = GATEWAY_STRIPE):
        self.id = payment_method_id
        self.user_id = user_id
        self.method_type = method_type
        self.gateway = gateway

        # Gateway integration details
        self.gateway_customer_id = None  # e.g., Stripe customer ID
        self.gateway_payment_method_id = None  # e.g., Stripe payment method ID

        # Card information (for display purposes only - last 4 digits)
        self.card_last_four = None
        self.card_brand = None  # visa, mastercard, amex, discover, etc.
        self.card_exp_month = None
        self.card_exp_year = None
        self.card_funding = None  # credit, debit, prepaid, unknown

        # PayPal information (for future use)
        self.paypal_email = None
        self.paypal_payer_id = None

        # Bank account information (for future use)
        self.bank_name = None
        self.bank_last_four = None
        self.bank_account_type = None  # checking, savings

        # Billing information
        self.billing_address_id = None  # Link to Address model
        self.cardholder_name = None

        # User-friendly details
        self.nickname = None  # e.g., "My Visa Card", "Work Card"
        self.is_default = False

        # Status
        self.is_active = True  # Can be deactivated without deleting

        # Timestamps
        self.created_at = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)
        self.last_used_at = None

    def to_dict(self, include_sensitive: bool = False) -> Dict[str, Any]:
        """Convert PaymentMethod to dictionary for Firestore storage"""
        data = {
            'id': self.id,
            'user_id': self.user_id,
            'method_type': self.method_type,
            'gateway': self.gateway,
            'card_last_four': self.card_last_four,
            'card_brand': self.card_brand,
            'card_exp_month': self.card_exp_month,
            'card_exp_year': self.card_exp_year,
            'card_funding': self.card_funding,
            'paypal_email': self.paypal_email,
            'bank_name': self.bank_name,
            'bank_last_four': self.bank_last_four,
            'bank_account_type': self.bank_account_type,
            'billing_address_id': self.billing_address_id,
            'cardholder_name': self.cardholder_name,
            'nickname': self.nickname,
            'is_default': self.is_default,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'last_used_at': self.last_used_at.isoformat() if self.last_used_at else None
        }

        # Include gateway-specific IDs only if sensitive data requested (for backend use)
        if include_sensitive:
            data['gateway_customer_id'] = self.gateway_customer_id
            data['gateway_payment_method_id'] = self.gateway_payment_method_id
            data['paypal_payer_id'] = self.paypal_payer_id

        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any], payment_method_id: str = None) -> 'PaymentMethod':
        """Create PaymentMethod from dictionary"""
        payment_method = cls(
            user_id=data['user_id'],
            payment_method_id=payment_method_id,
            method_type=data.get('method_type', cls.TYPE_CREDIT_CARD),
            gateway=data.get('gateway', cls.GATEWAY_STRIPE)
        )

        # Restore gateway integration
        payment_method.gateway_customer_id = data.get('gateway_customer_id')
        payment_method.gateway_payment_method_id = data.get('gateway_payment_method_id')

        # Restore card information
        payment_method.card_last_four = data.get('card_last_four')
        payment_method.card_brand = data.get('card_brand')
        payment_method.card_exp_month = data.get('card_exp_month')
        payment_method.card_exp_year = data.get('card_exp_year')
        payment_method.card_funding = data.get('card_funding')

        # Restore PayPal information
        payment_method.paypal_email = data.get('paypal_email')
        payment_method.paypal_payer_id = data.get('paypal_payer_id')

        # Restore bank information
        payment_method.bank_name = data.get('bank_name')
        payment_method.bank_last_four = data.get('bank_last_four')
        payment_method.bank_account_type = data.get('bank_account_type')

        # Restore billing information
        payment_method.billing_address_id = data.get('billing_address_id')
        payment_method.cardholder_name = data.get('cardholder_name')

        # Restore user-friendly details
        payment_method.nickname = data.get('nickname')
        payment_method.is_default = data.get('is_default', False)
        payment_method.is_active = data.get('is_active', True)

        # Restore timestamps
        if 'created_at' in data:
            payment_method.created_at = datetime.fromisoformat(data['created_at'])
        if 'updated_at' in data:
            payment_method.updated_at = datetime.fromisoformat(data['updated_at'])
        if data.get('last_used_at'):
            payment_method.last_used_at = datetime.fromisoformat(data['last_used_at'])

        return payment_method

    def save(self) -> str:
        """Save payment method to Firestore"""
        db = get_db()
        self.updated_at = datetime.now(timezone.utc)
        data = self.to_dict(include_sensitive=True)
        data.pop('id', None)

        if self.id:
            db.collection('payment_methods').document(self.id).set(data)
            return self.id
        else:
            doc_ref = db.collection('payment_methods').add(data)[1]
            self.id = doc_ref.id
            return self.id

    @classmethod
    def get_by_id(cls, payment_method_id: str) -> Optional['PaymentMethod']:
        """Get payment method by ID"""
        db = get_db()
        doc = db.collection('payment_methods').document(payment_method_id).get()

        if doc.exists:
            return cls.from_dict(doc.to_dict(), payment_method_id)
        return None

    @classmethod
    def get_by_user_id(cls, user_id: str, active_only: bool = True) -> List['PaymentMethod']:
        """Get all payment methods for a user"""
        db = get_db()
        query = db.collection('payment_methods').where(filter=FieldFilter('user_id', '==', user_id))

        if active_only:
            query = query.where(filter=FieldFilter('is_active', '==', True))

        docs = query.stream()
        payment_methods = [cls.from_dict(doc.to_dict(), doc.id) for doc in docs]

        # Sort by default first, then by last used, then by created date
        payment_methods.sort(key=lambda pm: (
            not pm.is_default,
            pm.last_used_at is None,
            -(pm.last_used_at.timestamp() if pm.last_used_at else 0),
            -pm.created_at.timestamp()
        ))

        return payment_methods

    @classmethod
    def get_default_by_user_id(cls, user_id: str) -> Optional['PaymentMethod']:
        """Get the default payment method for a user"""
        db = get_db()
        docs = db.collection('payment_methods')\
            .where(filter=FieldFilter('user_id', '==', user_id))\
            .where(filter=FieldFilter('is_default', '==', True))\
            .where(filter=FieldFilter('is_active', '==', True))\
            .limit(1)\
            .stream()

        for doc in docs:
            return cls.from_dict(doc.to_dict(), doc.id)
        return None

    def delete(self) -> bool:
        """
        Delete payment method from Firestore.
        Note: Consider using deactivate() instead for audit trail.
        """
        if not self.id:
            return False

        db = get_db()
        db.collection('payment_methods').document(self.id).delete()
        return True

    # Payment Method Management

    def set_as_default(self) -> None:
        """
        Set this payment method as the default for the user.
        Unsets any other default payment methods for this user.
        """
        if not self.user_id:
            return

        # Get all user payment methods and unset their default flag
        user_payment_methods = self.get_by_user_id(self.user_id, active_only=False)
        for pm in user_payment_methods:
            if pm.id != self.id and pm.is_default:
                pm.is_default = False
                pm.save()

        # Set this payment method as default
        self.is_default = True
        self.save()

    def deactivate(self) -> None:
        """Deactivate payment method without deleting (maintains history)"""
        self.is_active = False
        self.updated_at = datetime.now(timezone.utc)

        # If this was the default, unset it
        if self.is_default:
            self.is_default = False

    def reactivate(self) -> None:
        """Reactivate a deactivated payment method"""
        self.is_active = True
        self.updated_at = datetime.now(timezone.utc)

    def mark_as_used(self) -> None:
        """Update the last used timestamp"""
        self.last_used_at = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)

    # Validation

    def validate(self) -> List[str]:
        """
        Validate payment method fields and return list of validation errors.
        Returns empty list if validation passes.
        """
        errors = []

        if not self.user_id:
            errors.append("User ID is required")

        valid_types = [
            self.TYPE_CREDIT_CARD, self.TYPE_DEBIT_CARD, self.TYPE_PAYPAL,
            self.TYPE_BANK_ACCOUNT, self.TYPE_OTHER
        ]
        if self.method_type not in valid_types:
            errors.append(f"Invalid method type. Must be one of: {', '.join(valid_types)}")

        valid_gateways = [self.GATEWAY_STRIPE, self.GATEWAY_PAYPAL, self.GATEWAY_MANUAL]
        if self.gateway not in valid_gateways:
            errors.append(f"Invalid gateway. Must be one of: {', '.join(valid_gateways)}")

        # Validate card information if it's a card type
        if self.method_type in [self.TYPE_CREDIT_CARD, self.TYPE_DEBIT_CARD]:
            if not self.card_last_four:
                errors.append("Card last four digits are required for card payment methods")
            elif len(self.card_last_four) != 4:
                errors.append("Card last four must be exactly 4 digits")

            if not self.card_brand:
                errors.append("Card brand is required for card payment methods")

            if self.card_exp_month is not None:
                if not (1 <= self.card_exp_month <= 12):
                    errors.append("Card expiration month must be between 1 and 12")

            if self.card_exp_year is not None:
                current_year = datetime.now(timezone.utc).year
                if self.card_exp_year < current_year:
                    errors.append("Card has expired")

        # Validate PayPal information
        if self.method_type == self.TYPE_PAYPAL:
            if not self.paypal_email:
                errors.append("PayPal email is required for PayPal payment methods")

        return errors

    def is_valid(self) -> bool:
        """Check if payment method is valid"""
        return len(self.validate()) == 0

    def is_expired(self) -> bool:
        """Check if card is expired"""
        if self.method_type not in [self.TYPE_CREDIT_CARD, self.TYPE_DEBIT_CARD]:
            return False

        if not self.card_exp_month or not self.card_exp_year:
            return False

        now = datetime.now(timezone.utc)
        # Card expires at the end of the expiration month
        if self.card_exp_year < now.year:
            return True
        if self.card_exp_year == now.year and self.card_exp_month < now.month:
            return True

        return False

    # Display Methods

    def get_display_name(self) -> str:
        """Get a user-friendly display name for the payment method"""
        if self.nickname:
            return self.nickname

        if self.method_type in [self.TYPE_CREDIT_CARD, self.TYPE_DEBIT_CARD]:
            if self.card_brand and self.card_last_four:
                brand = self.card_brand.title()
                return f"{brand} ending in {self.card_last_four}"
            return "Card"

        if self.method_type == self.TYPE_PAYPAL:
            if self.paypal_email:
                return f"PayPal ({self.paypal_email})"
            return "PayPal"

        if self.method_type == self.TYPE_BANK_ACCOUNT:
            if self.bank_name and self.bank_last_four:
                return f"{self.bank_name} ending in {self.bank_last_four}"
            return "Bank Account"

        return self.method_type.replace('_', ' ').title()

    def get_masked_number(self) -> Optional[str]:
        """Get masked card/account number for display"""
        if self.method_type in [self.TYPE_CREDIT_CARD, self.TYPE_DEBIT_CARD]:
            if self.card_last_four:
                return f"**** **** **** {self.card_last_four}"

        if self.method_type == self.TYPE_BANK_ACCOUNT:
            if self.bank_last_four:
                return f"****{self.bank_last_four}"

        return None

    def get_expiration_display(self) -> Optional[str]:
        """Get formatted expiration date (MM/YY)"""
        if self.method_type not in [self.TYPE_CREDIT_CARD, self.TYPE_DEBIT_CARD]:
            return None

        if not self.card_exp_month or not self.card_exp_year:
            return None

        # Display as MM/YY format
        month = str(self.card_exp_month).zfill(2)
        year = str(self.card_exp_year)[-2:]  # Last 2 digits of year
        return f"{month}/{year}"

    def to_summary_dict(self) -> Dict[str, Any]:
        """Get a summary dictionary for API responses (excludes sensitive data)"""
        return {
            'id': self.id,
            'method_type': self.method_type,
            'display_name': self.get_display_name(),
            'masked_number': self.get_masked_number(),
            'card_brand': self.card_brand,
            'expiration': self.get_expiration_display(),
            'is_default': self.is_default,
            'is_active': self.is_active,
            'is_expired': self.is_expired()
        }
