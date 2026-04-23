from django.contrib.auth import get_user_model

User = get_user_model()


def get_username(strategy, details, backend, user=None, *args, **kwargs):
    """Генерує username з email для нових Google-користувачів."""
    if user:
        return
    email = details.get('email', '')
    return {'username': email[:150]}


def create_user(strategy, details, backend, user=None, *args, **kwargs):
    """Створює нового CustomUser із даних Google OAuth."""
    if user:
        return {'is_new': False}

    email = details.get('email')
    if not email:
        return

    new_user = User(
        email=email,
        username=kwargs.get('username', email[:150]),
        first_name=details.get('first_name', ''),
        last_name=details.get('last_name', ''),
    )
    new_user.set_unusable_password()
    new_user.save()

    return {'is_new': True, 'user': new_user}
