# -*- coding: utf-8 -*-
import sys, io, logging
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
logging.basicConfig(level=logging.INFO, stream=sys.stdout)
from modules.auto_parser import AutoParser
p = AutoParser()
data = p.parse_pdf('data/144758.pdf')
print(f"\nFine pitches: {data.fine_pitches}")
