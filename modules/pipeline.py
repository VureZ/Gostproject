# -*- coding: utf-8 -*-
"""
Полный пайплайн: PDF -> AutoParser -> GostSpec -> DesignationGenerator -> SQL.
Связывает все модули в единый процесс обработки ГОСТ.
"""

import os
import sys
import logging
from typing import Optional, Tuple, List, Dict

from modules.auto_parser import AutoParser, ParsedGostData
from modules.designation_generator import GostSpec, DesignationGenerator
from modules.database import GostDatabase

logger = logging.getLogger(__name__)


class GostPipeline:
    """Полный пайплайн обработки PDF ГОСТа."""

    def __init__(self):
        self.parser = AutoParser()
        self.parsed_data: Optional[ParsedGostData] = None
        self.spec: Optional[GostSpec] = None
        self.designations: List[Dict] = []
        self.parameters: List[Dict] = []

    def run_interactive(self, pdf_path: str) -> Tuple[int, int]:
        """Интерактивный режим: парсит PDF, запрашивает шаблон, пишет в SQL."""

        # Шаг 1: Парсинг PDF
        print(f"\n[1/5] Парсинг PDF: {pdf_path}")
        self.parsed_data = self.parser.parse_pdf(pdf_path)
        self._print_parsed_summary()

        # Шаг 2: Ввод шаблона пользователем
        print(f"\n[2/5] Шаблон обозначения")
        template_coarse, template_fine = self._ask_template()

        # Шаг 3: Ввод материалов/покрытий
        print(f"\n[3/5] Материалы и покрытия")
        mat_groups, st_grades, coats, coat_thick = self._ask_materials()

        # Шаг 4: Генерация
        print(f"\n[4/5] Генерация обозначений...")
        self.spec = self._build_spec(
            material_groups=mat_groups,
            steel_grades=st_grades,
            coatings=coats,
            coating_thicknesses=coat_thick,
        )
        self.spec.format_coarse = template_coarse
        self.spec.format_fine = template_fine
        gen = DesignationGenerator(self.spec)
        self.designations = gen.generate_all()
        self._print_generation_summary()

        # Подтверждение
        ans = input(f"\n  Записать {len(self.designations)} обозначений в SQL? (y/n): ").strip().lower()
        if ans != 'y':
            print("  Отменено.")
            return (0, 0)

        # Шаг 5: SQL
        self.parameters = self._build_parameters()
        return self._write_to_sql()

    def run(self, pdf_path: str,
            template_coarse: str = "",
            template_fine: str = "",
            material_groups: Optional[Dict] = None,
            steel_grades: Optional[Dict] = None,
            coatings: Optional[Dict] = None,
            coating_thicknesses: Optional[List[str]] = None,
            ) -> Tuple[int, int]:
        """
        Полный цикл: PDF -> парсинг -> генерация -> SQL.

        Args:
            pdf_path: путь к PDF файлу
            template_coarse: шаблон для крупного шага
            template_fine: шаблон для мелкого шага
            material_groups: группы материалов {"код": "carbon"|"stainless"}
            steel_grades: марки стали {"код_группы": ["марка1", ...]}
            coatings: покрытия {"код": "описание"}
            coating_thicknesses: толщины покрытий ["6", "9", "12"]
        Returns:
            (кол-во обозначений, кол-во параметров) записанных в SQL
        """
        # Шаг 1: Парсинг PDF
        print(f"\n[1/4] Парсинг PDF: {pdf_path}")
        self.parsed_data = self.parser.parse_pdf(pdf_path)
        print(f"  ГОСТ: {self.parsed_data.gost_number}")
        print(f"  Изделие: {self.parsed_data.product_name}")
        print(f"  Диаметров: {len(self.parsed_data.diameters)}")
        print(f"  Крупных шагов: {len(self.parsed_data.coarse_pitches)}")
        print(f"  Мелких шагов: {len(self.parsed_data.fine_pitches)}")
        print(f"  Размеров S: {len(self.parsed_data.wrench_sizes)}")
        if self.parsed_data.designation_examples:
            print(f"  Примеры обозначений:")
            for ex in self.parsed_data.designation_examples[:3]:
                print(f"    {ex}")

        # Шаг 2: Построение GostSpec из данных парсера
        print(f"\n[2/4] Построение спецификации...")
        self.spec = self._build_spec(
            material_groups=material_groups,
            steel_grades=steel_grades,
            coatings=coatings,
            coating_thicknesses=coating_thicknesses,
        )
        print(f"  Групп материалов: {len(self.spec.material_groups)}")
        print(f"  Покрытий: {len(self.spec.coatings)}")

        # Применяем шаблоны обозначений
        if template_coarse:
            self.spec.format_coarse = template_coarse
        if template_fine:
            self.spec.format_fine = template_fine

        # Шаг 3: Генерация всех комбинаций
        print(f"\n[3/4] Генерация обозначений...")
        gen = DesignationGenerator(self.spec)
        self.designations = gen.generate_all()
        print(f"  Сгенерировано: {len(self.designations)} обозначений")
        if self.designations:
            print(f"  Примеры:")
            for d in self.designations[:3]:
                print(f"    {d['FullDesignation']}")
            if len(self.designations) > 6:
                print(f"    ...")
                print(f"    {self.designations[-1]['FullDesignation']}")

        # Подготовка параметров для SQL
        self.parameters = self._build_parameters()

        # Шаг 4: Запись в SQL
        return self._write_to_sql()

    def _build_spec(self, material_groups=None, steel_grades=None,
                    coatings=None, coating_thicknesses=None) -> GostSpec:
        """Строит GostSpec из ParsedGostData + пользовательских данных."""
        d = self.parsed_data
        spec = GostSpec()
        spec.gost_number = d.gost_number
        spec.product_name = d.product_name
        spec.diameters = d.diameters
        spec.coarse_pitches = d.coarse_pitches
        spec.fine_pitches = d.fine_pitches
        spec.wrench_sizes = d.wrench_sizes

        # Допуск — по умолчанию 6Н для гаек
        spec.tolerance = "Н"

        # Материалы — из аргументов или стандартный набор
        if material_groups is not None:
            spec.material_groups = material_groups
        else:
            spec.material_groups = {
                "4": "carbon", "5": "carbon", "6": "carbon",
                "8": "carbon", "10": "carbon", "12": "carbon",
            }

        # Марки стали
        if steel_grades is not None:
            spec.steel_grades = steel_grades
        else:
            spec.steel_grades = {
                "6": ["А12"],
                "8": ["35", "35Х", "38ХА"],
                "10": ["20", "20Х", "40Х"],
                "12": ["40Х", "30ХГСА"],
            }

        # Покрытия
        if coatings is not None:
            spec.coatings = coatings
        else:
            spec.coatings = {
                "01": "Цинковое хроматированное",
                "02": "Кадмиевое хроматированное",
                "03": "Многослойное медь-никель",
                "05": "Окисное",
                "06": "Фосфатное",
                "09": "Цинковое",
            }

        # Толщины покрытий
        if coating_thicknesses is not None:
            spec.coating_thicknesses = coating_thicknesses
        else:
            spec.coating_thicknesses = ["6", "9", "12"]

        spec.executions = ["1", "2"]
        return spec

    def _build_parameters(self) -> List[Dict]:
        """Строит строки параметров из ParsedGostData для SQL."""
        d = self.parsed_data
        rows = []
        gost = d.gost_number

        for diameter in d.diameters:
            coarse = d.coarse_pitches.get(diameter, "")
            fine_list = d.fine_pitches.get(diameter, [])
            s_val = d.wrench_sizes.get(diameter, "")
            e_val = d.e_min_values.get(diameter)
            da_min = d.da_min_values.get(diameter)
            da_max = d.da_max_values.get(diameter)
            dw_min = d.dw_min_values.get(diameter)
            m_val = d.m_values.get(diameter)
            mass = d.mass_data.get(diameter)

            # Строка для крупного шага (или без шага если парсер не нашёл)
            if coarse or not fine_list:
                rows.append({
                    'GOST_Number': gost,
                    'ThreadDiameter': float(diameter),
                    'ThreadPitch': coarse,
                    'PitchType': 'coarse',
                    'MaterialGroup': '',
                    'Parameter_da_min': da_min,
                    'Parameter_da_max': da_max,
                    'Parameter_dw_min': dw_min,
                    'Parameter_e_min': e_val,
                    'Parameter_m_max': m_val,
                    'Parameter_m_min': None,
                    'Parameter_m_prime_min': None,
                    'Parameter_S_nom_max': float(s_val) if s_val else None,
                    'Parameter_S_min': None,
                    'TheoreticalMass': mass,
                })

            # Строки для мелких шагов
            for fine_pitch in fine_list:
                rows.append({
                    'GOST_Number': gost,
                    'ThreadDiameter': float(diameter),
                    'ThreadPitch': fine_pitch,
                    'PitchType': 'fine',
                    'MaterialGroup': '',
                    'Parameter_da_min': da_min,
                    'Parameter_da_max': da_max,
                    'Parameter_dw_min': dw_min,
                    'Parameter_e_min': e_val,
                    'Parameter_m_max': m_val,
                    'Parameter_m_min': None,
                    'Parameter_m_prime_min': None,
                    'Parameter_S_nom_max': float(s_val) if s_val else None,
                    'Parameter_S_min': None,
                    'TheoreticalMass': None,
                })
        return rows

    # ================================================================
    # Интерактивный ввод шаблона
    # ================================================================
    def _print_parsed_summary(self):
        d = self.parsed_data
        print(f"  ГОСТ: {d.gost_number}")
        print(f"  Изделие: {d.product_name}")
        print(f"  Диаметров: {len(d.diameters)}: {', '.join(d.diameters[:8])}{'...' if len(d.diameters) > 8 else ''}")
        print(f"  Крупных шагов: {len(d.coarse_pitches)}")
        print(f"  Мелких шагов: {len(d.fine_pitches)}")
        print(f"  Размеров S: {len(d.wrench_sizes)}")
        if d.designation_examples:
            print(f"  Примеры обозначений из PDF:")
            for ex in d.designation_examples[:3]:
                print(f"    {ex}")

    def _ask_template(self) -> Tuple[str, str]:
        """Запрашивает шаблон обозначения у пользователя."""
        print("  Доступные переменные для шаблона:")
        print("    {product}    - название изделия (Гайка, Болт...)")
        print("    {gost}       - номер ГОСТ")
        print("    {diameter}   - диаметр резьбы")
        print("    {pitch}      - шаг резьбы (мелкий)")
        print("    {group}      - класс прочности / группа материала")
        print("    {steel_grade}- марка стали")
        print("    {coating}    - код покрытия с толщиной")
        print("    {s}          - размер под ключ S")
        print()
        print("  Примеры шаблонов:")
        print("    1. Гайка М{diameter}-6Н.{group}[.{steel_grade}][.{coating}] (S{s}) ГОСТ 15524-70")
        print("    2. {product} ГОСТ {gost}-M{diameter}-{group}")
        print("    3. Свой шаблон")
        print()

        choice = input("  Выберите (1/2/3) или введите шаблон: ").strip()

        if choice == '1':
            tc = "{product} М{diameter}-6Н.{group}{steel_part}{coating_part} (S{s}) ГОСТ {gost}"
            tf = "{product} 2М{diameter} × {pitch}—6Н.{group}{steel_part}{coating_part} ГОСТ {gost}"
        elif choice == '2':
            tc = "{product} ГОСТ {gost}-M{diameter}-{group}"
            tf = "{product} ГОСТ {gost}-M{diameter}x{pitch}-{group}"
        elif choice == '3' or len(choice) > 3:
            template = choice if len(choice) > 3 else input("  Шаблон (крупный шаг): ").strip()
            tc = template
            tf = input("  Шаблон (мелкий шаг, Enter=тот же): ").strip() or template
        else:
            tc = ""
            tf = ""

        print(f"  Шаблон крупный: {tc}")
        print(f"  Шаблон мелкий:  {tf}")
        return tc, tf

    def _ask_materials(self) -> Tuple[Dict, Dict, Dict, List]:
        """Запрашивает материалы и покрытия."""
        print("  Использовать стандартный набор материалов? (по ГОСТ 1759.0)")
        print("    Классы: 4, 5, 6, 8, 10, 12")
        print("    Покрытия: 01, 02, 03, 05, 06, 09 с толщинами 6, 9, 12 мкм")
        ans = input("  Стандартный набор? (y/n): ").strip().lower()
        if ans == 'y' or ans == '':
            return None, None, None, None

        # Ввод групп материалов
        print("\n  Группы материалов (код=тип, тип: carbon или stainless)")
        print("  Пример: 5=carbon, 6=carbon, 8=carbon")
        print("  Пустая строка = конец ввода")
        groups = {}
        while True:
            s = input("    > ").strip()
            if not s:
                break
            if '=' in s:
                k, v = s.split('=', 1)
                groups[k.strip()] = v.strip()
        # Пустой dict = пользователь не ввёл групп (без материалов)
        # None = использовать стандартный набор

        # Ввод марок стали
        print("\n  Марки стали (группа=марка1,марка2)")
        print("  Пример: 8=35,35Х,38ХА")
        grades = {}
        while True:
            s = input("    > ").strip()
            if not s:
                break
            if '=' in s:
                k, v = s.split('=', 1)
                grades[k.strip()] = [x.strip() for x in v.split(',') if x.strip()]

        # Ввод покрытий
        print("\n  Покрытия (код=описание)")
        print("  Пример: 01=Цинковое")
        print("  Пустая строка = без покрытий")
        coats = {}
        while True:
            s = input("    > ").strip()
            if not s:
                break
            if '=' in s:
                k, v = s.split('=', 1)
                coats[k.strip()] = v.strip()

        # Толщины
        thick_str = input("\n  Толщины покрытий через запятую (напр: 6,9,12, пусто = без): ").strip()
        thick = [x.strip() for x in thick_str.split(',') if x.strip()] if thick_str else []

        return groups, grades, coats, thick

    def _print_generation_summary(self):
        print(f"  Сгенерировано: {len(self.designations)} обозначений")
        if self.designations:
            print(f"  Примеры:")
            for d in self.designations[:3]:
                print(f"    {d['FullDesignation']}")
            if len(self.designations) > 6:
                print(f"    ...")
                print(f"    {self.designations[-1]['FullDesignation']}")

    def _write_to_sql(self) -> Tuple[int, int]:
        print(f"\n[5/5] Запись в SQL Server...")
        db = GostDatabase()
        if not db.connect():
            print("  ОШИБКА: не удалось подключиться к SQL Server!")
            return (0, 0)
        try:
            dc = db.insert_designations(self.designations, clear_existing=True)
            print(f"  Обозначений записано: {dc}")
            pc = 0
            if self.parameters:
                pc = db.insert_parameters(self.parameters, clear_existing=True)
                print(f"  Параметров записано: {pc}")
            # Сохраняем CSV
            self._save_csv()
            print(f"  ГОТОВО!")
            return (dc, pc)
        except Exception as e:
            print(f"  Ошибка SQL: {e}")
            return (0, 0)
        finally:
            db.disconnect()

    def _save_csv(self):
        """Сохраняет обозначения в CSV-файл."""
        if not self.designations or not self.spec:
            return
        from modules.config import OUTPUT_DIR
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        safe = self.spec.gost_number.replace(' ', '_').replace('-', '_')
        path = os.path.join(OUTPUT_DIR, f'designations_{safe}.csv')
        cols = ['GOST_Number', 'FullDesignation', 'ThreadSize',
                'MaterialGroup', 'Coating', 'SteelGrade',
                'ThreadDiameter', 'ThreadPitch']
        with open(path, 'w', encoding='utf-8') as f:
            f.write(";".join(cols) + "\n")
            for d in self.designations:
                f.write(";".join([str(d.get(c, '')) for c in cols]) + "\n")
        print(f"  CSV: {path}")
