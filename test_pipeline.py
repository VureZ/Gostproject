# -*- coding: utf-8 -*-
"""Тест пайплайна с шаблоном (неинтерактивный)."""
import sys, os, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import logging
logging.basicConfig(level=logging.WARNING, stream=sys.stderr)

from modules.pipeline import GostPipeline

# Тест с шаблоном 1 (ГОСТ 15524-70)
print("=" * 60)
print("ТЕСТ: шаблон 1 для ГОСТ 15524-70")
print("=" * 60)
pipe = GostPipeline()
pipe.parsed_data = pipe.parser.parse_pdf("data/144758.pdf")
pipe.spec = pipe._build_spec()

# Шаблон 1
pipe.spec.format_coarse = "{product} М{diameter}-6Н.{group}{steel_part}{coating_part} (S{s}) ГОСТ {gost}"
pipe.spec.format_fine = "{product} 2М{diameter} × {pitch}—6Н.{group}{steel_part}{coating_part} ГОСТ {gost}"

from modules.designation_generator import DesignationGenerator
gen = DesignationGenerator(pipe.spec)
desigs = gen.generate_all()

print(f"Обозначений: {len(desigs)}")
print(f"\nПримеры (без покрытия/марки):")
for d in desigs[:3]:
    print(f"  {d['FullDesignation']}")

print(f"\nПримеры (с маркой стали):")
with_steel = [d for d in desigs if d['SteelGrade']]
for d in with_steel[:3]:
    print(f"  {d['FullDesignation']}")

print(f"\nПримеры (с покрытием):")
with_coat = [d for d in desigs if d['Coating'] and not d['SteelGrade']]
for d in with_coat[:3]:
    print(f"  {d['FullDesignation']}")

print(f"\nПримеры (мелкий шаг):")
fine = [d for d in desigs if '2M' in d['ThreadSize']]
for d in fine[:3]:
    print(f"  {d['FullDesignation']}")

# Тест шаблона 2 (ISO 4036)
print(f"\n{'=' * 60}")
print("ТЕСТ: шаблон 2 для ГОСТ ISO 4036-2014")
print("=" * 60)
pipe2 = GostPipeline()
pipe2.parsed_data = pipe2.parser.parse_pdf("data/138714.pdf")
pipe2.spec = pipe2._build_spec(
    material_groups={"St": "carbon"},
    steel_grades={}, coatings={}, coating_thicknesses=[],
)
pipe2.spec.format_coarse = "{product} ГОСТ {gost}-M{diameter}-{group}"
pipe2.spec.format_fine = "{product} ГОСТ {gost}-M{diameter}x{pitch}-{group}"

gen2 = DesignationGenerator(pipe2.spec)
desigs2 = gen2.generate_all()
print(f"Обозначений: {len(desigs2)}")
for d in desigs2[:5]:
    print(f"  {d['FullDesignation']}")
