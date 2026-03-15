# -*- coding: utf-8 -*-
"""
Данные из ГОСТ ISO 4036-2014
Гайки шестигранные низкие без фаски (тип 0).
Класс точности В.
Резьба от М1,6 до М10.
Данные извлечены автоматически из PDF (138714.pdf).
"""

from modules.designation_generator import GostSpec


def get_gost_iso_4036_2014() -> GostSpec:
    """Returns complete specification for GOST ISO 4036-2014."""

    spec = GostSpec()
    spec.gost_number = "ISO 4036-2014"
    spec.product_name = "Гайка шестигранная низкая"
    spec.tolerance = "—"  # Класс точности B

    # ===== Таблица 1: Размеры (стр.8 PDF) =====
    # (M3,5) — не рекомендуется, но включаем
    spec.diameters = [
        "1.6", "2", "2.5", "3", "3.5", "4", "5", "6", "8", "10"
    ]

    # ===== Крупный шаг (P) — из Таблицы 1 =====
    spec.coarse_pitches = {
        "1.6": "0.35", "2": "0.4", "2.5": "0.45", "3": "0.5",
        "3.5": "0.6", "4": "0.7", "5": "0.8", "6": "1",
        "8": "1.25", "10": "1.5"
    }

    # Мелкий шаг не определён в этом ГОСТ
    spec.fine_pitches = {}

    # ===== Материал (из раздела 5 «Обозначение», стр.9 PDF) =====
    # Обозначение: Гайка ... ГОСТ ISO 4036-M{d}-{материал}
    # Материал: St (сталь), нержавеющая сталь, цветной металл
    # В ГОСТ ISO 4036 нет классов прочности как в 15524-70
    # Используем обозначение материала напрямую
    spec.material_groups = {
        "St": "carbon",
    }

    spec.steel_grades = {}

    # Покрытия — в данном ГОСТ не входят в обозначение
    spec.coatings = {}

    # Формат обозначения (из раздела 5, стр.9 PDF):
    # "Гайка шестигранная низкая ГОСТ ISO 4036-M6-St"
    spec.format_coarse = "{product} ГОСТ {gost}-M{diameter}-{group}"
    spec.format_fine = "{product} ГОСТ {gost}-M{diameter}x{pitch}-{group}"

    return spec


def get_parameters_iso_4036_2014():
    """
    Возвращает строки параметров из Таблицы 1 (стр.8 PDF).
    """
    # Колонки: D, P, e_min, m_max, m_min, s_nom, s_min
    table_data = [
        ("1.6", "0.35", 3.28,  1.00, 0.75,  3.20, 2.90),
        ("2",   "0.4",  4.18,  1.20, 0.95,  4.00, 3.70),
        ("2.5", "0.45", 5.31,  1.60, 1.35,  5.00, 4.70),
        ("3",   "0.5",  5.88,  1.80, 1.55,  5.50, 5.20),
        ("3.5", "0.6",  6.44,  2.00, 1.75,  6.00, 5.70),
        ("4",   "0.7",  7.50,  2.20, 1.95,  7.00, 6.64),
        ("5",   "0.8",  8.63,  2.70, 2.45,  8.00, 7.64),
        ("6",   "1",   10.89,  3.20, 2.90, 10.00, 9.64),
        ("8",   "1.25",14.20,  4.00, 3.70, 13.00,12.57),
        ("10",  "1.5", 17.59,  5.00, 4.70, 16.00,15.57),
    ]

    rows = []
    gost = "ISO 4036-2014"

    for d, p, e_min, m_max, m_min, s_nom, s_min in table_data:
        rows.append({
            'GOST_Number': gost,
            'ThreadDiameter': float(d),
            'ThreadPitch': p,
            'PitchType': 'coarse',
            'MaterialGroup': '',
            'Parameter_da_min': None,
            'Parameter_da_max': None,
            'Parameter_dw_min': None,
            'Parameter_e_min': float(e_min),
            'Parameter_m_max': float(m_max),
            'Parameter_m_min': float(m_min),
            'Parameter_m_prime_min': None,
            'Parameter_S_nom_max': float(s_nom),
            'Parameter_S_min': float(s_min),
            'TheoreticalMass': None,
        })

    return rows
