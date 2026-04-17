from django.contrib.auth import get_user_model
import os

User = get_user_model()
username = 'admin'
email = 'admin@mwt.one'
password = 'MuitoWork2026?'

if not User.objects.filter(username=username).exists():
    User.objects.create_superuser(username, email, password)
    print(f"Superuser {username} created successfully.")
else:
    user = User.objects.get(username=username)
    user.set_password(password)
    user.is_superuser = True
    user.is_staff = True
    user.save()
    print(f"Superuser {username} updated successfully.")
