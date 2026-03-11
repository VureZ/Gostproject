# -*- coding: utf-8 -*-
"""Отладка: что видит OCR на странице с таблицей."""
import sys, os, io
os.environ['FLAGS_use_mkldnn'] = '0'
os.environ['FLAGS_use_onednn'] = '0'
os.environ['PADDLE_USE_ONEDNN'] = '0'
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from modules.auto_parser import AutoParser

parser = AutoParser(use_gpu=False)
data = parser.parse_pdf('data/144758.pdf', dpi=300)

# Выведем текст страницы 3 (индекс 2) — там таблица
print("\n=== СТРАНИЦА 3 (текст OCR) ===")
if len(parser.pages_text) >= 3:
    print(parser.pages_text[2])
else:
    print("Нет страницы 3")
