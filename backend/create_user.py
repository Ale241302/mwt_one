import django
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.base')
django.setup()
from django.contrib.auth import get_user_model
User = get_user_model()
User.objects.filter(username='admin').delete()
u = User.objects.create_superuser('admin', 'admin@mwt.one', 'password')
u.is_api_user = True
u.save()
print("User 'admin' created and enabled for API.")
