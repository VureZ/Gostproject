# Test auto_parser
import os, sys
os.environ['FLAGS_use_mkldnn'] = '0'
os.environ['FLAGS_use_onednn'] = '0'

from modules.auto_parser import AutoParser

for pdf in ['data/144758.pdf', 'data/138714.pdf']:
    print("=" * 60)
    p = AutoParser()
    r = p.parse_pdf(pdf)
    print(p.get_summary())
    print(f"Pitches coarse: {r['pitches_coarse']}")
    print(f"Pitches fine: {r['pitches_fine']}")
    print()
