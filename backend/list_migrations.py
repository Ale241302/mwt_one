from django.db import connection
with connection.cursor() as cursor:
    cursor.execute("SELECT app, name FROM django_migrations WHERE name LIKE '000%' ORDER BY app, name")
    rows = cursor.fetchall()
    for app, name in rows:
        print(f"App: {app}, Name: {name}")
