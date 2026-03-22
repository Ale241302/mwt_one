import sys
import os
import traceback

# Add backend to path
sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()

try:
    from apps.expedientes import enums_exp
    print(f"enums file: {enums_exp.__file__}")
    from apps.expedientes.enums_artifacts import ArtifactStatusEnum
    print(f"Success! ArtifactStatusEnum: {ArtifactStatusEnum}")
    
    print("\nAttempting to import apps.expedientes.services...")
    import apps.expedientes.services
    print("Success!")
except Exception:
    traceback.print_exc()
