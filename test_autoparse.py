# -*- coding: utf-8 -*-
import sys, io, logging, traceback
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
logging.basicConfig(level=logging.INFO, stream=sys.stderr)

from modules.auto_parser import AutoParser

for pdf in ['data/144758.pdf', 'data/138714.pdf']:
    print("=" * 60)
    print(f"PDF: {pdf}")
    print("=" * 60)
    try:
        p = AutoParser()
        data = p.parse_pdf(pdf)
        print(p.get_summary())
    except Exception as e:
        print(f"ОШИБКА: {e}")
        traceback.print_exc()
    print()
