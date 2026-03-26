import os
import re

tests_dir = 'apps/expedientes/tests'
files = [os.path.join(tests_dir, f) for f in os.listdir(tests_dir) if f.endswith('.py')]

for fpath in files:
    with open(fpath, 'r', encoding='utf-8') as f:
        content = f.read()
        
    old_content = content
    content = content.replace("self.client.post(url, {'payload': {}})", "self.client.post(url, {'payload': {}}, format='json')")
    # Also catch other common ones like self.client.post(url, {'some': 'data'}) if they exist without format='json'
    # but the previous script already did data, payload. The only ones failing are dict literals.
    content = re.sub(r'self\.client\.post\(([^,]+),\s*(\{[^}]+\})\)', r"self.client.post(\1, \2, format='json')", content)
    
    if old_content != content:
        with open(fpath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f'Modified {fpath}')
