import re
from pathlib import Path

p = Path('templates/revisao_categorias.html')
s = p.read_text(encoding='utf-8')

m = re.search(r"<script>([\s\S]*?)</script>", s)
if not m:
    print('No script tag found')
    raise SystemExit(1)

script = m.group(1)

open_braces = script.count('{')
close_braces = script.count('}')
print('Braces { :', open_braces, ' } :', close_braces)

tries = len(re.findall(r"\btry\s*\{", script))
catches = len(re.findall(r"\bcatch\s*\(", script))
finallys = len(re.findall(r"\bfinally\b", script))
print('try:', tries, 'catch:', catches, 'finally:', finallys)

if open_braces != close_braces:
    print('MISMATCH braces')
else:
    print('Braces appear balanced')

if tries > catches + finallys:
    print('Possible try without catch/finally')
else:
    print('All try blocks have catch/finally')
