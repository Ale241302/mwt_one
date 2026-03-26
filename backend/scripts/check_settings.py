import os
import traceback
import sys

print(f"Working Directory: {os.getcwd()}")
print(f"PYTHONPATH: {sys.path}")

try:
    from config.settings import base
    print(f"BASE_DIR according to base: {base.BASE_DIR}")
    print(f"SECRET_KEY: {base.SECRET_KEY[:5]}...")
    
    from config.settings import test
    print("Successfully imported test settings")
    print(f"Test DB Name: {test.DATABASES['default']['NAME']}")
except Exception:
    traceback.print_exc()
