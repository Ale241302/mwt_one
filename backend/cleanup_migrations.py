print("--- START CLEANUP SCRIPT ---")
from django.db import connection
with connection.cursor() as cursor:
    apps_to_clean = ['agreements', 'commercial', 'pricing', 'users', 'productos', 'notifications', 'expedientes']
    for app in apps_to_clean:
        print(f"Cleaning migrations for {app}...")
        cursor.execute("DELETE FROM django_migrations WHERE app=%s AND name >= '0003'", [app])
    cursor.execute("DELETE FROM django_migrations WHERE app='brands' AND name='0005_brand_id_brandtechnicalsheet'")
print("--- END CLEANUP SCRIPT ---")
