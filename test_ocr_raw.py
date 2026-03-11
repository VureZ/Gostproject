# -*- coding: utf-8 -*-
"""Отладка: сырые OCR-данные страницы 3."""
import sys, os, io, json
os.environ['FLAGS_use_mkldnn'] = '0'
os.environ['FLAGS_use_onednn'] = '0'
os.environ['PADDLE_USE_ONEDNN'] = '0'
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from modules.auto_parser import AutoParser

parser = AutoParser(use_gpu=False)
data = parser.parse_pdf('data/144758.pdf', dpi=300)

# Сырые OCR элементы страницы 3 (индекс 2)
print("\n=== Сырые OCR элементы стр.3 ===")
items = parser.pages_ocr_data[2]
# Группируем в строки
items.sort(key=lambda x: x['cy'])
rows = []
cur_row = [items[0]]
cur_y = items[0]['cy']
for it in items[1:]:
    if abs(it['cy'] - cur_y) <= 15:
        cur_row.append(it)
    else:
        cur_row.sort(key=lambda x: x['cx'])
        rows.append(cur_row)
        cur_row = [it]
        cur_y = it['cy']
if cur_row:
    cur_row.sort(key=lambda x: x['cx'])
    rows.append(cur_row)

for i, row in enumerate(rows):
    texts = [it['text'] for it in row]
    joined = ' '.join(texts)
    # Считаем числа
    import re
    nums = re.findall(r'\b(\d+(?:[.,]\d+)?)\b', joined)
    print(f"  Строка {i:2d} ({len(row):2d} эл, {len(nums):2d} чисел): {joined[:120]}")
