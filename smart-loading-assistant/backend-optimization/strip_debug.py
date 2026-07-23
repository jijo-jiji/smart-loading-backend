import re

with open('app/main.py', 'r') as f:
    lines = f.readlines()

cleaned = [line for line in lines if 'print(f"DEBUG:' not in line and "print(f'DEBUG:" not in line]

with open('app/main.py', 'w') as f:
    f.writelines(cleaned)

removed = len(lines) - len(cleaned)
print(f"Removed {removed} debug print lines.")
