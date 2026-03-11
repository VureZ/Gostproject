# -*- coding: utf-8 -*-
import sys, os, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import logging
logging.basicConfig(level=logging.WARNING, stream=sys.stderr)
from modules.pipeline import GostPipeline
from modules.designation_generator import DesignationGenerator

pipe = GostPipeline()
pipe.parsed_data = pipe.parser.parse_pdf("data/144758.pdf")
pipe.spec = pipe._build_spec()
pipe.spec.format_coarse = "{product} М{diameter}-6Н.{group}{steel_part}{coating_part} (S{s}) ГОСТ {gost}"
pipe.spec.format_fine = "{product} 2М{diameter} x {pitch}-6Н.{group}{steel_part}{coating_part} ГОСТ {gost}"

print(f"Fine pitches: {pipe.spec.fine_pitches}")
print(f"Format fine: {pipe.spec.format_fine}")

gen = DesignationGenerator(pipe.spec)
desigs = gen.generate_all()
fine = [d for d in desigs if d['ThreadPitch'] and 'x' in d['ThreadSize'].lower()]
print(f"\nМелких обозначений: {len(fine)}")
for d in fine[:5]:
    print(f"  {d['FullDesignation']} | size={d['ThreadSize']} pitch={d['ThreadPitch']}")
