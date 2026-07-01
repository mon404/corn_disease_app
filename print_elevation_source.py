import sys
import os
import inspect
import kivymd.uix.behaviors.elevation

# Find the file path
file_path = inspect.getfile(kivymd.uix.behaviors.elevation)
print("File path:", file_path)

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Let's find the KV string
import re
kv_match = re.search(r'Builder\.load_string\(\s*"""(.*?)"""\s*\)', content, re.DOTALL)
if kv_match:
    print("Found KV block:")
    print(kv_match.group(1)[:2000])
else:
    print("KV block not found using regex.")
    # Let's print around line 20-100 where it might be defined
    lines = content.split('\n')
    print("Showing first 150 lines of elevation.py:")
    print('\n'.join(lines[:150]))

sys.exit(0)
