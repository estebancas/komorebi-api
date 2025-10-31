"""
Assign admin role to a user by email
"""
from app.services.firebase_service import initialize_firebase
from app.models.user import User
from app.models.role import Role


def assign_admin_role(email: str):
    """Assign admin role to a user"""
    initialize_firebase()

    # Get user
    user = User.get_by_email(email)
    if not user:
        print(f"Error: User with email '{email}' not found")
        return

    # Get or create admin role
    admin_role = Role.get_by_name('admin')
    if not admin_role:
        print("Admin role not found. Creating it...")
        admin_role = Role(name='admin')
        admin_role.save()
        print(f"Admin role created with ID: {admin_role.id}")

    # Check if user already has admin role
    if user.has_role(admin_role.id):
        print(f"User '{email}' already has admin role")
        return

    # Add admin role
    user.add_role(admin_role.id)
    user.save()

    print(f"Success: Admin role assigned to '{email}'")
    print(f"User roles: {[role.name for role in user.get_roles()]}")


if __name__ == '__main__':
    import sys
    if len(sys.argv) < 2:
        print("Usage: python scripts/assign_admin.py <email>")
        sys.exit(1)

    email = sys.argv[1]
    assign_admin_role(email)
