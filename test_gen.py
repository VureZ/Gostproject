# -*- coding: utf-8 -*-
"""Тест генерации обозначений для ГОСТ 15524-70 и ГОСТ ISO 4036-2014."""
import sys, os, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from data.gost_15524_70 import get_gost_15524_70, get_parameters_15524_70
from data.gost_iso_4036_2014 import get_gost_iso_4036_2014, get_parameters_iso_4036_2014
from modules.designation_generator import DesignationGenerator

print("=" * 60)
print("ТЕСТ: ГОСТ 15524-70")
print("=" * 60)
spec = get_gost_15524_70()
gen = DesignationGenerator(spec)
designations = gen.generate_all()
print(f"Всего обозначений: {len(designations)}")
print(f"\nПримеры (первые 10):")
for d in designations[:10]:
    print(f"  {d['FullDesignation']}")
print(f"\nПримеры (мелкий шаг):")
fine = [d for d in designations if d['ThreadPitch'] and '2M' in d['ThreadSize']]
for d in fine[:5]:
    print(f"  {d['FullDesignation']}")
print(f"\nПримеры (с маркой стали):")
steel = [d for d in designations if d['SteelGrade']]
for d in steel[:5]:
    print(f"  {d['FullDesignation']}")

print(f"\nПараметры: {len(get_parameters_15524_70())} строк")

print("\n" + "=" * 60)
print("ТЕСТ: ГОСТ ISO 4036-2014")
print("=" * 60)
spec2 = get_gost_iso_4036_2014()
gen2 = DesignationGenerator(spec2)
designations2 = gen2.generate_all()
print(f"Всего обозначений: {len(designations2)}")
print(f"\nПримеры:")
for d in designations2[:10]:
    print(f"  {d['FullDesignation']}")

print(f"\nПараметры: {len(get_parameters_iso_4036_2014())} строк")

input("\nНажмите Enter для выхода...")
