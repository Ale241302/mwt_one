import os
from backend.config.settings.base import BASE_DIR
print(f"BASE_DIR: {BASE_DIR}")
test_db = os.path.join(BASE_DIR, 'db_test_write.sqlite3')
try:
    with open(test_db, 'w') as f:
        f.write('test')
    print(f"Successfully wrote to {test_db}")
    os.remove(test_db)
except Exception as e:
    print(f"Failed to write to {test_db}: {e}")
