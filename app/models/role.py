from datetime import datetime, timezone
from typing import Optional, Dict, Any
from app.services.firebase_service import get_db


class Role:
    def __init__(self, name: str, role_id: Optional[str] = None):
        self.id = role_id
        self.name = name.strip()
        self.created_at = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)
    
    @staticmethod
    def validate_name(name: str) -> bool:
        if not name or not name.strip():
            return False
        if len(name.strip()) < 2:
            return False
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'name': self.name,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any], role_id: str = None):
        role = cls(
            name=data['name'],
            role_id=role_id
        )
        
        if 'created_at' in data:
            role.created_at = datetime.fromisoformat(data['created_at'])
        if 'updated_at' in data:
            role.updated_at = datetime.fromisoformat(data['updated_at'])
            
        return role
    
    def save(self) -> str:
        if not self.validate_name(self.name):
            raise ValueError("Role name must be at least 2 characters long")
            
        db = get_db()
        data = self.to_dict()
        data.pop('id', None)
        self.updated_at = datetime.now(timezone.utc)
        data['updated_at'] = self.updated_at.isoformat()
        
        if self.id:
            db.collection('roles').document(self.id).set(data)
            return self.id
        else:
            doc_ref = db.collection('roles').add(data)[1]
            self.id = doc_ref.id
            return self.id
    
    @classmethod
    def get_by_id(cls, role_id: str) -> Optional['Role']:
        db = get_db()
        doc = db.collection('roles').document(role_id).get()
        
        if doc.exists:
            return cls.from_dict(doc.to_dict(), role_id)
        return None
    
    @classmethod
    def get_by_name(cls, name: str) -> Optional['Role']:
        db = get_db()
        docs = db.collection('roles').where('name', '==', name.strip()).limit(1).stream()
        
        for doc in docs:
            return cls.from_dict(doc.to_dict(), doc.id)
        return None
    
    @classmethod
    def get_all(cls) -> list['Role']:
        db = get_db()
        docs = db.collection('roles').stream()
        
        return [cls.from_dict(doc.to_dict(), doc.id) for doc in docs]
    
    def delete(self) -> bool:
        if not self.id:
            return False
            
        db = get_db()
        db.collection('roles').document(self.id).delete()
        return True