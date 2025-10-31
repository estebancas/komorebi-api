from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
import bcrypt
from email_validator import validate_email, EmailNotValidError
from google.cloud.firestore_v1.base_query import FieldFilter
from app.services.firebase_service import get_db
from app.models.role import Role


class User:
    def __init__(self, email: str, password: str = None, user_id: Optional[str] = None,
                 first_name: str = "", last_name: str = "", role_ids: List[str] = None):
        self.id = user_id
        self.email = email.lower()
        self.first_name = first_name
        self.last_name = last_name
        self.password_hash = None
        self.role_ids = role_ids or []
        self.created_at = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)

        if password:
            self.set_password(password)

    def set_password(self, password: str):
        salt = bcrypt.gensalt()
        self.password_hash = bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

    def check_password(self, password: str) -> bool:
        if not self.password_hash:
            return False
        return bcrypt.checkpw(password.encode('utf-8'), self.password_hash.encode('utf-8'))

    @staticmethod
    def validate_email(email: str) -> bool:
        try:
            validate_email(email)
            return True
        except EmailNotValidError:
            return False

    def to_dict(self, include_sensitive: bool = False, include_roles: bool = False) -> Dict[str, Any]:
        data = {
            'id': self.id,
            'email': self.email,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'role_ids': self.role_ids,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

        if include_sensitive:
            data['password_hash'] = self.password_hash

        if include_roles:
            data['roles'] = [role.name for role in self.get_roles()]

        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any], user_id: str = None):
        user = cls(
            email=data['email'],
            user_id=user_id,
            first_name=data.get('first_name', ''),
            last_name=data.get('last_name', ''),
            role_ids=data.get('role_ids', [])
        )

        user.password_hash = data.get('password_hash')

        if 'created_at' in data:
            user.created_at = datetime.fromisoformat(data['created_at'])
        if 'updated_at' in data:
            user.updated_at = datetime.fromisoformat(data['updated_at'])

        return user

    def save(self) -> str:
        db = get_db()
        data = self.to_dict(include_sensitive=True)
        data.pop('id', None)
        self.updated_at = datetime.now(timezone.utc)
        data['updated_at'] = self.updated_at.isoformat()

        if self.id:
            db.collection('users').document(self.id).set(data)
            return self.id
        else:
            doc_ref = db.collection('users').add(data)[1]
            self.id = doc_ref.id
            return self.id

    @classmethod
    def get_by_id(cls, user_id: str) -> Optional['User']:
        db = get_db()
        doc = db.collection('users').document(user_id).get()

        if doc.exists:
            return cls.from_dict(doc.to_dict(), user_id)
        return None

    @classmethod
    def get_by_email(cls, email: str) -> Optional['User']:
        db = get_db()
        docs = db.collection('users').where(filter=FieldFilter('email', '==', email.lower())).limit(1).stream()

        for doc in docs:
            return cls.from_dict(doc.to_dict(), doc.id)
        return None

    def delete(self) -> bool:
        if not self.id:
            return False

        db = get_db()
        db.collection('users').document(self.id).delete()
        return True

    def add_role(self, role_id: str) -> bool:
        if role_id not in self.role_ids:
            self.role_ids.append(role_id)
            return True
        return False

    def remove_role(self, role_id: str) -> bool:
        if role_id in self.role_ids:
            self.role_ids.remove(role_id)
            return True
        return False

    def has_role(self, role_id: str) -> bool:
        return role_id in self.role_ids

    def get_roles(self) -> List['Role']:
        roles = []
        for role_id in self.role_ids:
            role = Role.get_by_id(role_id)
            if role:
                roles.append(role)
        return roles

    def has_role_name(self, role_name: str) -> bool:
        for role_id in self.role_ids:
            role = Role.get_by_id(role_id)
            if role and role.name == role_name:
                return True
        return False

    @classmethod
    def get_all(cls, include_roles: bool = False) -> List['User']:
        db = get_db()
        docs = db.collection('users').stream()

        users = []
        for doc in docs:
            user = cls.from_dict(doc.to_dict(), doc.id)
            if include_roles:
                # Pre-populate roles to avoid N+1 queries in API responses
                user._roles = user.get_roles()
            users.append(user)

        return users