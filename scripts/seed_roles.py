"""
Role management script
"""
import sys
from app.services.firebase_service import initialize_firebase
from app.models.role import Role


def create_role(name):
    """Create a new role with the given name"""
    # Initialize Firebase
    initialize_firebase()

    # Validate role name
    if not Role.validate_name(name):
        print(f"Error: Role name must be at least 2 characters long")
        sys.exit(1)

    # Check if role already exists
    existing_role = Role.get_by_name(name)
    if existing_role:
        print(f"Error: Role '{name}' already exists (ID: {existing_role.id})")
        sys.exit(1)

    # Create the role
    try:
        role = Role(name=name)
        role_id = role.save()
        print(f"Success: Role '{name}' created with ID: {role_id}")
    except Exception as e:
        print(f"Error creating role: {str(e)}")
        sys.exit(1)


def list_roles():
    """List all existing roles"""
    # Initialize Firebase
    initialize_firebase()

    try:
        roles = Role.get_all()
        if roles:
            print(f"\nFound {len(roles)} role(s):")
            print("-" * 50)
            for role in roles:
                print(f"  - {role.name:<20} (ID: {role.id})")
            print("-" * 50)
        else:
            print("No roles found in database")
    except Exception as e:
        print(f"Error listing roles: {str(e)}")
        sys.exit(1)
