# -*- coding: utf-8 -*-
"""Тест автоматического парсинга PDF через PaddleOCR."""
import sys, os, io
os.environ['FLAGS_use_mkldnn'] = '0'
os.environ['FLAGS_use_onednn'] = '0'
os.environ['PADDLE_USE_ONEDNN'] = '0'
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from modules.auto_parser import AutoParser

# Тестируем на ГОСТ 15524-70
print("=" * 60)
print("Парсинг: 144758.pdf (ГОСТ 15524-70)")
print("=" * 60)
parser = AutoParser(use_gpu=False)
data = parser.parse_pdf('data/144758.pdf', dpi=300)
print(f"\n{parser.get_summary()}")
print(f"\nДиаметры ({len(data['table_data']['diameters'])}): "
      f"{data['table_data']['diameters']}")
print(f"Крупные шаги: {data['table_data']['coarse_pitches']}")
print(f"Мелкие шаги: {data['table_data']['fine_pitches']}")
print(f"Размеры S: {data['table_data']['wrench_sizes']}")
print(f"Высоты m: {data['table_data']['m_values']}")
