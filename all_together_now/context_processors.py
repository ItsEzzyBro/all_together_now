# all_together_now/context_processors.py

def user_role(request):
    """
    Makes the user's role (Admin, Leader, etc.) available in all templates as {{ user_role }}.
    """
    role = None

    # Only check if user is logged in
    if request.user.is_authenticated:
        # Try to read a role directly from the user model
        role = getattr(request.user, "role", None)

        # If the role is stored on a related profile model, check there too
        if role is None and hasattr(request.user, "profile"):
            role = getattr(request.user.profile, "role_name", None)

        # Fallbacks for built-in Django flags
        if request.user.is_superuser or request.user.is_staff:
            role = role or "Admin"

    return {"user_role": role}
