from django.db import connection
with connection.cursor() as cursor:
    cursor.execute("DELETE FROM django_migrations WHERE app='agreements' AND name='0004_creditclockrule'")
    print("Deleted migration record for agreements.0004")
