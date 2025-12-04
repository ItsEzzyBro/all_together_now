# all_together_now/context_processors.py

def get_user_accessible_ministries(user):
    """
    Get ministries the user has access to based on their roles.
    Church Administrators have access to all ministries.
    """
    from member_management.models import UsersAndRoles, Role, RolesAndMinistries
    from ministry.models import Ministry
    
    if not user.is_authenticated:
        return Ministry.objects.none()
    
    # Check if user has Church Administrator role
    try:
        church_admin_role = Role.objects.get(role_name="Church Administrator")
        is_church_admin = UsersAndRoles.objects.filter(
            user=user, 
            role=church_admin_role
        ).exists()
        
        if is_church_admin:
            return Ministry.objects.all()
    except Role.DoesNotExist:
        pass
    
    # Get user's roles
    user_roles = UsersAndRoles.objects.filter(user=user).values_list('role_id', flat=True)
    
    # Get ministries associated with those roles
    ministry_ids = RolesAndMinistries.objects.filter(
        role_id__in=user_roles
    ).values_list('ministry_id', flat=True)
    
    return Ministry.objects.filter(id__in=ministry_ids)


def user_role(request):
    """
    Makes the user's role (Admin, Leader, etc.) available in all templates as {{ user_role }}.
    Also provides {{ is_church_admin }} to check if user has Church Administrator role.
    Auto-assigns Church Administrator role to superusers if not already assigned.
    """
    role = None
    is_church_admin = False

    # Only check if user is logged in
    if request.user.is_authenticated:
        from member_management.models import UsersAndRoles, Role
        
        # Ensure Church Administrator role exists
        church_admin_role, _ = Role.objects.get_or_create(role_name="Church Administrator")
        
        # If user is superuser, auto-assign Church Administrator role
        if request.user.is_superuser:
            UsersAndRoles.objects.get_or_create(user=request.user, role=church_admin_role)
        
        # Check if user has Church Administrator role
        is_church_admin = UsersAndRoles.objects.filter(
            user=request.user, 
            role=church_admin_role
        ).exists()
        
        # Try to read a role directly from the user model
        role = getattr(request.user, "role", None)

        # If the role is stored on a related profile model, check there too
        if role is None and hasattr(request.user, "profile"):
            role = getattr(request.user.profile, "role_name", None)

        # Fallbacks for built-in Django flags
        if request.user.is_superuser or request.user.is_staff:
            role = role or "Admin"

    return {"user_role": role, "is_church_admin": is_church_admin}
