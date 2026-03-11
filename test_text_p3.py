# -*- coding: utf-8 -*-
import sys, os, io, fitz
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
doc = fitz.open('data/144758.pdf')
# Страница 3 (индекс 2) — таблица
text = doc[2].get_text()
lines = text.split('\n')
for i, line in enumerate(lines):
    if line.strip():
        print(f"{i:3d}: {line.rstrip()[:120]}")
doc.close()
