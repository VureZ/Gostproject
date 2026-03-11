# -*- coding: utf-8 -*-
import sys, io, logging
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
logging.basicConfig(level=logging.WARNING, stream=sys.stderr)

from modules.auto_parser import AutoParser

p = AutoParser()
data = p.parse_pdf('data/144758.pdf')
print("Мелкий шаг (все):")
for d, pitches in sorted(data.fine_pitches.items(), key=lambda x: float(x[0])):
    print(f"  d={d}: {pitches}")

print(f"\nЭталон из ГОСТ:")
print("  d=8: 1, d=10: нет(или 1), d=12: 1.25, d=14: 1.25")
print("  d=16: 1.5, d=18: 1.5, d=20: 1.5, d=22: 2, d=24: 2")
print("  d=27: 2, d=36: 2, d=42: 3, d=48: 3")
