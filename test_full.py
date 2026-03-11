# -*- coding: utf-8 -*-
"""Полный тест: генерация обозначений и запись в SQL."""
import sys, os, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from data.gost_15524_70 import get_gost_15524_70, get_parameters_15524_70
from data.gost_iso_4036_2014 import get_gost_iso_4036_2014, get_parameters_iso_4036_2014
from modules.designation_generator import DesignationGenerator
from modules.database import GostDatabase

db = GostDatabase()
if not db.connect():
    print("ОШИБКА: нет SQL Server!")
    sys.exit(1)
print("SQL Server подключён\n")

# === ГОСТ 15524-70 ===
print("=" * 50)
print("ГОСТ 15524-70")
print("=" * 50)
spec1 = get_gost_15524_70()
gen1 = DesignationGenerator(spec1)
desigs1 = gen1.generate_all()
print(f"Сгенерировано обозначений: {len(desigs1)}")

dc1 = db.insert_designations(desigs1, clear_existing=True)
print(f"Записано обозначений: {dc1}")

params1 = get_parameters_15524_70()
pc1 = db.insert_parameters(params1, clear_existing=True)
print(f"Записано параметров: {pc1}")

# === ГОСТ ISO 4036-2014 ===
print("\n" + "=" * 50)
print("ГОСТ ISO 4036-2014")
print("=" * 50)
spec2 = get_gost_iso_4036_2014()
gen2 = DesignationGenerator(spec2)
desigs2 = gen2.generate_all()
print(f"Сгенерировано обозначений: {len(desigs2)}")

dc2 = db.insert_designations(desigs2, clear_existing=True)
print(f"Записано обозначений: {dc2}")

params2 = get_parameters_iso_4036_2014()
pc2 = db.insert_parameters(params2, clear_existing=True)
print(f"Записано параметров: {pc2}")

# === Итого ===
print("\n" + "=" * 50)
total_d = db.get_designation_count()
print(f"ИТОГО в БД: {total_d} обозначений")

# Примеры из БД
db.cursor.execute("SELECT TOP 5 FullDesignation FROM ProductDesignations WHERE GOST_Number = '15524-70' ORDER BY ID")
print("\nПримеры ГОСТ 15524-70:")
for row in db.cursor.fetchall():
    print(f"  {row[0]}")

db.cursor.execute("SELECT TOP 5 FullDesignation FROM ProductDesignations WHERE GOST_Number = 'ISO 4036-2014' ORDER BY ID")
print("\nПримеры ГОСТ ISO 4036-2014:")
for row in db.cursor.fetchall():
    print(f"  {row[0]}")

db.disconnect()
print("\nГОТОВО!")
