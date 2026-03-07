import os
import re

tests_dir = 'apps/expedientes/tests'
files = [os.path.join(tests_dir, f) for f in os.listdir(tests_dir) if f.endswith('.py')]

for fpath in files:
    with open(fpath, 'r', encoding='utf-8') as f:
        content = f.read()
        
    old_content = content
    content = re.sub(r'self\.client\.post\(([^,]+),\s*(\{[^}]*\})\)', r"self.client.post(\1, \2, format='json')", content)
    content = re.sub(r'self\.client\.post\(([^,]+),\s*payload\)', r"self.client.post(\1, payload, format='json')", content)
    content = re.sub(r'self\.client\.post\(([^,]+),\s*data\)', r"self.client.post(\1, data, format='json')", content)
    
    if old_content != content:
        with open(fpath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f'Modified {fpath}')
