import subprocess
import sys
with open('out_clean.txt', 'w', encoding='utf-8') as f:
    res = subprocess.run([sys.executable, 'test_nova.py'], stderr=subprocess.STDOUT, stdout=subprocess.PIPE, text=True)
    f.write(res.stdout)
