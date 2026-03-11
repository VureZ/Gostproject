# -*- coding: utf-8 -*-
import sys, io, os
os.environ['FLAGS_use_mkldnn'] = '0'
os.environ['FLAGS_use_onednn'] = '0'
os.environ['PADDLE_USE_ONEDNN'] = '0'
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
print('Python:', sys.version)
mods = ['paddle', 'paddleocr', 'fitz', 'cv2', 'numpy', 'PIL', 'pyodbc']
for m in mods:
    try:
        mod = __import__(m)
        ver = getattr(mod, '__version__', getattr(mod, 'version', 'OK'))
        print(f'  {m}: {ver}')
    except Exception as e:
        print(f'  {m}: MISSING ({e})')
