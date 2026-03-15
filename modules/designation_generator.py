# -*- coding: utf-8 -*-
"""
Generator uslovnyh oboznachenij izdelijj po GOST.
Generiruet VSE vozmozhnye kombinacii oboznachenij.
"""

import logging
from typing import List, Dict, Optional
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class GostSpec:
    """Specification of a GOST standard."""
    gost_number: str = ""
    product_name: str = ""
    diameters: List[str] = field(default_factory=list)
    coarse_pitches: Dict[str, str] = field(default_factory=dict)
    fine_pitches: Dict[str, List[str]] = field(default_factory=dict)
    material_groups: Dict[str, str] = field(default_factory=dict)
    steel_grades: Dict[str, List[str]] = field(default_factory=dict)
    coatings: Dict[str, str] = field(default_factory=dict)
    tolerance: str = "6H"
    format_coarse: str = ""
    format_fine: str = ""
    # Дополнительные поля для ГОСТ 15524-70 и подобных
    wrench_sizes: Dict[str, str] = field(default_factory=dict)  # d -> S
    coating_thicknesses: List[str] = field(default_factory=list)  # ["6", "9", "12"]
    executions: List[str] = field(default_factory=list)  # ["1", "2"]


class DesignationGenerator:
    """Generates all possible designations for a GOST spec."""
    
    def __init__(self, spec: GostSpec):
        self.spec = spec
        self.designations = []
    
    def generate_all(self) -> List[Dict]:
        """Generate all valid designation combinations."""
        self.designations = []
        
        for diameter in self.spec.diameters:
            self._generate_coarse(diameter)
            self._generate_fine(diameter)
        
        logger.info("Generated %d designations", len(self.designations))
        return self.designations
    
    def _generate_coarse(self, diameter: str):
        """Generate designations with coarse pitch."""
        pitch = self.spec.coarse_pitches.get(diameter, "")
        if not pitch and self.spec.coarse_pitches:
            # Проверяем: если для большинства диаметров крупный шаг есть,
            # а для этого нет — скорее всего парсер не нашёл.
            # Генерируем всё равно (крупный шаг не указывается в обозначении).
            # Пропускаем только если у диаметра есть мелкий шаг (значит крупного реально нет)
            has_fine = diameter in self.spec.fine_pitches and self.spec.fine_pitches[diameter]
            has_most_coarse = len(self.spec.coarse_pitches) > len(self.spec.diameters) * 0.5
            if has_fine and not has_most_coarse:
                return  # Действительно нет крупного шага
            # Иначе продолжаем генерацию (pitch будет пустым)

        for group, stype in self.spec.material_groups.items():
            # Список марок стали для данной группы (может быть пустой)
            grades_for_group = self.spec.steel_grades.get(group, [])

            # --- Варианты БЕЗ марки стали (углеродистая / без указания) ---
            self._add_with_coatings(diameter, "", pitch, group, "", stype)

            # --- Варианты С маркой стали (легированная / нержавеющая) ---
            for grade in grades_for_group:
                self._add_with_coatings(diameter, "", pitch, group, grade, stype)

    def _generate_fine(self, diameter: str):
        """Generate designations with fine pitch."""
        for pitch in self.spec.fine_pitches.get(diameter, []):
            for group, stype in self.spec.material_groups.items():
                grades_for_group = self.spec.steel_grades.get(group, [])

                # Без марки стали
                self._add_with_coatings(diameter, pitch, pitch, group, "", stype)

                # С маркой стали
                for grade in grades_for_group:
                    self._add_with_coatings(diameter, pitch, pitch, group, grade, stype)

    def _add_with_coatings(self, diameter, pitch, pitch_val, group, grade, stype):
        """Генерирует вариант без покрытия + все варианты с покрытиями."""
        # Без покрытия
        self._add(diameter, pitch, pitch_val, group, grade, "")
        # С каждым покрытием
        for coat_code in self.spec.coatings:
            if self.spec.coating_thicknesses:
                for thick in self.spec.coating_thicknesses:
                    self._add(diameter, pitch, pitch_val, group, grade, coat_code + thick)
            else:
                self._add(diameter, pitch, pitch_val, group, grade, coat_code)
    
    def _add(self, diameter, pitch, pitch_val, group, grade, coating):
        """Build designation string and add to list."""
        s = self.spec
        has_fmt = (pitch and s.format_fine) or (not pitch and s.format_coarse)

        if has_fmt:
            # Используем пользовательский шаблон
            fmt = s.format_fine if pitch else s.format_coarse
            # Формируем опциональные части
            steel_part = f".{grade}" if grade else ""
            coating_part = f".{coating}" if coating else ""
            wrench = s.wrench_sizes.get(diameter, "")
            try:
                full = fmt.format(
                    product=s.product_name, gost=s.gost_number,
                    diameter=diameter, pitch=pitch or "",
                    group=group, steel_grade=grade, coating=coating,
                    steel_part=steel_part, coating_part=coating_part,
                    s=wrench,
                )
            except KeyError as e:
                # Неизвестная переменная в шаблоне — fallback
                logger.warning(f"Неизвестная переменная в шаблоне: {e}")
                full = f"{s.product_name} M{diameter} ГОСТ {s.gost_number}"
            thread_size = f"M{diameter}x{pitch}" if pitch else f"M{diameter}"
        elif s.wrench_sizes:
            # Формат ГОСТ 15524-70:
            # Исп.1 (крупный): Гайка М{d}-6Н.{класс}[.{марка}][.{покр}] (S{s}) ГОСТ 15524-70
            # Исп.2 (мелкий): Гайка 2М{d} × {шаг}—6Н.{класс}[.{марка}][.{покр}] ГОСТ 15524-70
            wrench = s.wrench_sizes.get(diameter, "")
            gost_str = f"ГОСТ {s.gost_number}"

            if pitch:
                # Исполнение 2, мелкий шаг
                thread_part = f"2М{diameter} \u00d7 {pitch}"
                thread_size = f"2M{diameter}x{pitch}"
                params_parts = [group]
                if grade:
                    params_parts.append(grade)
                if coating:
                    params_parts.append(coating)
                params = ".".join(params_parts)
                full = f"{s.product_name} {thread_part}\u20146{s.tolerance}.{params} {gost_str}"
            else:
                # Исполнение 1, крупный шаг
                thread_part = f"М{diameter}"
                thread_size = f"M{diameter}"
                params_parts = [group]
                if grade:
                    params_parts.append(grade)
                if coating:
                    params_parts.append(coating)
                params = ".".join(params_parts)
                s_part = f" (S{wrench})" if wrench else ""
                full = f"{s.product_name} {thread_part}-6{s.tolerance}.{params}{s_part} {gost_str}"
        else:
            # Формат по умолчанию: Product M{d}[x{p}].{group}[.{grade}][.{coat}] GOST {num}
            thread_size = f"M{diameter}x{pitch}" if pitch else f"M{diameter}"
            parts = [p for p in [group, grade, coating] if p]
            params = ".".join(parts)
            gost_str = f"ГОСТ {s.gost_number}"
            if params:
                full = f"{s.product_name} {thread_size}.{params} {gost_str}"
            else:
                full = f"{s.product_name} {thread_size} {gost_str}"

        self.designations.append({
            'GOST_Number': s.gost_number,
            'FullDesignation': full,
            'ThreadSize': thread_size,
            'MaterialGroup': group,
            'Coating': coating,
            'SteelGrade': grade,
            'ThreadDiameter': float(diameter),
            'ThreadPitch': pitch_val or "",
        })
    
    def get_stats(self) -> str:
        return '\n'.join([
            f"GOST: {self.spec.gost_number}",
            f"Product: {self.spec.product_name}",
            f"Diameters: {len(self.spec.diameters)}",
            f"Material groups: {len(self.spec.material_groups)}",
            f"Coatings: {len(self.spec.coatings)}",
            f"Total designations: {len(self.designations)}",
        ])
