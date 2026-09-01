def user_profile(request):
    """Expose the current user's profile (and picture) to all templates."""
    if not getattr(request.user, 'is_authenticated', False):
        return {'user_profile': None}
    try:
        return {'user_profile': request.user.userprofile}
    except Exception:
        return {'user_profile': None}
