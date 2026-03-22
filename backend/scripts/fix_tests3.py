import os
import re

tests_dir = 'apps/expedientes/tests'
files = [os.path.join(tests_dir, f) for f in os.listdir(tests_dir) if f.endswith('.py')]

for fpath in files:
    with open(fpath, 'r', encoding='utf-8') as f:
        content = f.read()

    # The issue:
    # res = self.client.post(url, {})
    # res = self.client.post(url, {'payload': {}})
    # res = self.client.post(url, data)
    
    # We want to add format='json' at the end of the arguments list for self.client.post if it's not already there.
    
    # Simple strings replacements for empty lists/dicts:
    content = content.replace("self.client.post(url, {})", "self.client.post(url, {}, format='json')")
    content = content.replace("self.client.post(url, {'payload': {}})", "self.client.post(url, {'payload': {}}, format='json')")
    
    # Regex replacements:
    # Match `self.client.post(url, <something>)` where <something> doesn't contain `format='json'`
    content = re.sub(
        r"self\.client\.post\(([^,]+),\s*([^,)]+)\)", 
        r"self.client.post(\1, \2, format='json')", 
        content
    )
    
    # Let's fix cases that got doubled format='json' (just in case)
    content = content.replace(", format='json', format='json'", ", format='json'")

    with open(fpath, 'w', encoding='utf-8') as f:
        f.write(content)

print('Done applying format=json')
