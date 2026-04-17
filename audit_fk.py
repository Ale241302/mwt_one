import os, re
apps_dir = 'backend/apps'
for root, dirs, files in os.walk(apps_dir):
    if 'models.py' in files:
        path = os.path.join(root, 'models.py')
        app = os.path.basename(root)
        with open(path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        for i, line in enumerate(lines, 1):
            m = re.search(r'(ForeignKey|OneToOneField)\s*\(\s*[\"\']([a-z_]+\.[A-Z][A-Za-z0-9_]+)[\"\']', line)
            if m:
                print(f'{app}:{i}: {line.strip()}')
            m2 = re.search(r'(ForeignKey|OneToOneField)\s*\(\s*settings\.AUTH_USER_MODEL', line)
            if m2:
                print(f'{app}:{i}: {line.strip()}')
