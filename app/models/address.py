from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from google.cloud.firestore_v1.base_query import FieldFilter
from app.services.firebase_service import get_db


class Address:
    """
    Represents a user's address (shipping or billing) in the e-commerce system.
    Users can have multiple addresses, with one marked as default.
    """
    # Address type constants
    TYPE_SHIPPING = 'shipping'
    TYPE_BILLING = 'billing'
    TYPE_BOTH = 'both'

    def __init__(self, user_id: str, address_id: Optional[str] = None,
                 address_type: str = TYPE_SHIPPING):
        self.id = address_id
        self.user_id = user_id
        self.address_type = address_type

        # Recipient information
        self.recipient_name = ""
        self.phone_number = ""

        # Address details
        self.street_address_1 = ""
        self.street_address_2 = ""  # Optional: apartment, suite, unit, etc.
        self.city = ""
        self.state = ""  # State/Province/Region
        self.postal_code = ""
        self.country = ""

        # Additional flags
        self.is_default = False

        # Timestamps
        self.created_at = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)

    def to_dict(self) -> Dict[str, Any]:
        """Convert Address to dictionary for Firestore storage"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'address_type': self.address_type,
            'recipient_name': self.recipient_name,
            'phone_number': self.phone_number,
            'street_address_1': self.street_address_1,
            'street_address_2': self.street_address_2,
            'city': self.city,
            'state': self.state,
            'postal_code': self.postal_code,
            'country': self.country,
            'is_default': self.is_default,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any], address_id: str = None) -> 'Address':
        """Create Address from dictionary"""
        address = cls(
            user_id=data['user_id'],
            address_id=address_id,
            address_type=data.get('address_type', cls.TYPE_SHIPPING)
        )

        # Restore recipient information
        address.recipient_name = data.get('recipient_name', '')
        address.phone_number = data.get('phone_number', '')

        # Restore address details
        address.street_address_1 = data.get('street_address_1', '')
        address.street_address_2 = data.get('street_address_2', '')
        address.city = data.get('city', '')
        address.state = data.get('state', '')
        address.postal_code = data.get('postal_code', '')
        address.country = data.get('country', '')

        # Restore flags
        address.is_default = data.get('is_default', False)

        # Restore timestamps
        if 'created_at' in data:
            address.created_at = datetime.fromisoformat(data['created_at'])
        if 'updated_at' in data:
            address.updated_at = datetime.fromisoformat(data['updated_at'])

        return address

    def save(self) -> str:
        """Save address to Firestore"""
        db = get_db()
        self.updated_at = datetime.now(timezone.utc)
        data = self.to_dict()
        data.pop('id', None)

        if self.id:
            db.collection('addresses').document(self.id).set(data)
            return self.id
        else:
            doc_ref = db.collection('addresses').add(data)[1]
            self.id = doc_ref.id
            return self.id

    @classmethod
    def get_by_id(cls, address_id: str) -> Optional['Address']:
        """Get address by ID"""
        db = get_db()
        doc = db.collection('addresses').document(address_id).get()

        if doc.exists:
            return cls.from_dict(doc.to_dict(), address_id)
        return None

    @classmethod
    def get_by_user_id(cls, user_id: str) -> List['Address']:
        """Get all addresses for a user"""
        db = get_db()
        docs = db.collection('addresses')\
            .where(filter=FieldFilter('user_id', '==', user_id))\
            .stream()

        addresses = [cls.from_dict(doc.to_dict(), doc.id) for doc in docs]

        # Sort by default first, then by created_at descending
        addresses.sort(key=lambda a: (not a.is_default, -a.created_at.timestamp()))

        return addresses

    @classmethod
    def get_default_by_user_id(cls, user_id: str, address_type: Optional[str] = None) -> Optional['Address']:
        """
        Get the default address for a user, optionally filtered by type.
        If address_type is provided, returns the default address of that type.
        """
        db = get_db()
        query = db.collection('addresses')\
            .where(filter=FieldFilter('user_id', '==', user_id))\
            .where(filter=FieldFilter('is_default', '==', True))

        if address_type:
            # Get addresses matching the type or TYPE_BOTH
            all_defaults = [cls.from_dict(doc.to_dict(), doc.id) for doc in query.stream()]
            for address in all_defaults:
                if address.address_type == address_type or address.address_type == cls.TYPE_BOTH:
                    return address
            return None

        docs = query.limit(1).stream()
        for doc in docs:
            return cls.from_dict(doc.to_dict(), doc.id)
        return None

    def delete(self) -> bool:
        """Delete address from Firestore"""
        if not self.id:
            return False

        db = get_db()
        db.collection('addresses').document(self.id).delete()
        return True

    def set_as_default(self) -> None:
        """
        Set this address as the default for the user.
        Unsets any other default addresses for this user.
        """
        if not self.user_id:
            return

        # Get all user addresses and unset their default flag
        user_addresses = self.get_by_user_id(self.user_id)
        for address in user_addresses:
            if address.id != self.id and address.is_default:
                address.is_default = False
                address.save()

        # Set this address as default
        self.is_default = True
        self.save()

    def validate(self) -> List[str]:
        """
        Validate address fields and return list of validation errors.
        Returns empty list if validation passes.
        """
        errors = []

        if not self.recipient_name or not self.recipient_name.strip():
            errors.append("Recipient name is required")

        if not self.street_address_1 or not self.street_address_1.strip():
            errors.append("Street address is required")

        if not self.city or not self.city.strip():
            errors.append("City is required")

        if not self.state or not self.state.strip():
            errors.append("State/Province is required")

        if not self.postal_code or not self.postal_code.strip():
            errors.append("Postal code is required")

        if not self.country or not self.country.strip():
            errors.append("Country is required")

        if not self.phone_number or not self.phone_number.strip():
            errors.append("Phone number is required")

        if self.address_type not in [self.TYPE_SHIPPING, self.TYPE_BILLING, self.TYPE_BOTH]:
            errors.append(f"Invalid address type. Must be one of: {self.TYPE_SHIPPING}, {self.TYPE_BILLING}, {self.TYPE_BOTH}")

        return errors

    def is_valid(self) -> bool:
        """Check if address is valid"""
        return len(self.validate()) == 0

    def get_formatted_address(self) -> str:
        """
        Get address formatted as a multi-line string suitable for display or shipping labels.
        """
        lines = [
            self.recipient_name,
            self.street_address_1
        ]

        if self.street_address_2:
            lines.append(self.street_address_2)

        lines.append(f"{self.city}, {self.state} {self.postal_code}")
        lines.append(self.country)

        if self.phone_number:
            lines.append(f"Phone: {self.phone_number}")

        return "\n".join(lines)
