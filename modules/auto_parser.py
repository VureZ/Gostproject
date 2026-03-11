# -*- coding: utf-8 -*-
"""
Автоматический парсер PDF ГОСТов.
Извлекает данные из таблиц PDF через PyMuPDF (текстовый слой).
Если текстовый слой пуст/мусорный — использует PaddleOCR как fallback.
"""

import os
import re
import fitz
import logging
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class ParsedGostData:
    """Результат парсинга PDF ГОСТа."""
    gost_number: str = ""
    product_name: str = ""
    diameters: List[str] = field(default_factory=list)
    coarse_pitches: Dict[str, str] = field(default_factory=dict)
    fine_pitches: Dict[str, List[str]] = field(default_factory=dict)
    wrench_sizes: Dict[str, str] = field(default_factory=dict)
    e_min_values: Dict[str, float] = field(default_factory=dict)
    da_min_values: Dict[str, float] = field(default_factory=dict)
    da_max_values: Dict[str, float] = field(default_factory=dict)
    dw_min_values: Dict[str, float] = field(default_factory=dict)
    m_values: Dict[str, float] = field(default_factory=dict)
    m_max_values: Dict[str, float] = field(default_factory=dict)
    m_min_values: Dict[str, float] = field(default_factory=dict)
    s_nom_values: Dict[str, float] = field(default_factory=dict)
    s_min_values: Dict[str, float] = field(default_factory=dict)
    mass_data: Dict[str, float] = field(default_factory=dict)
    designation_examples: List[str] = field(default_factory=list)
    raw_pages_text: List[str] = field(default_factory=list)


class AutoParser:
    """Автопарсер PDF ГОСТов — извлекает данные из таблиц."""

    def __init__(self):
        self.data = ParsedGostData()

    def parse_pdf(self, pdf_path: str) -> ParsedGostData:
        """Главный метод: парсит PDF и возвращает извлечённые данные."""
        logger.info(f"Парсинг PDF: {pdf_path}")
        self._pdf_path = os.path.abspath(pdf_path)
        self._doc = fitz.open(pdf_path)

        # Шаг 1: Извлечь текст со всех страниц
        pages_text = []
        for i in range(self._doc.page_count):
            text = self._doc[i].get_text()
            text = self._fix_encoding(text)
            pages_text.append(text)
        self.data.raw_pages_text = pages_text

        full_text = '\n'.join(pages_text)

        # Шаг 2: Определить номер ГОСТ
        self.data.gost_number = self._find_gost_number(full_text)
        logger.info(f"ГОСТ: {self.data.gost_number}")

        # Шаг 3: Определить тип изделия
        self.data.product_name = self._find_product_name(full_text)
        logger.info(f"Изделие: {self.data.product_name}")

        # Шаг 4: Найти и разобрать таблицу размеров
        # Попытка 1: текстовый подход (надёжный для большинства таблиц)
        for page_text in pages_text:
            if self._try_parse_dimension_table(page_text):
                break

        # Попытка 2: bbox-подход для уточнения мелких шагов
        if self.data.diameters:
            self._fix_fine_pitches_via_bbox()
        else:
            # Попытка 3: bbox-подход с нуля (для стандартных таблиц)
            for page_idx in range(self._doc.page_count):
                if self._try_parse_dimension_table_bbox(page_idx):
                    break

        # Шаг 5: Найти примеры обозначений
        self._find_designation_examples(full_text)

        self._doc.close()
        self._doc = None

        logger.info(f"Найдено: {len(self.data.diameters)} диаметров, "
                    f"{len(self.data.coarse_pitches)} крупных шагов, "
                    f"{len(self.data.fine_pitches)} мелких шагов, "
                    f"{len(self.data.wrench_sizes)} размеров S")
        return self.data

    # ================================================================
    # Поиск номера ГОСТ
    # ================================================================
    def _find_gost_number(self, text: str) -> str:
        patterns = [
            r'ГОСТ\s+ISO\s+([\d]+[\s—\-–]+\d+)',
            r'ГОСТ\s+([\d]+[\s—\-–]+\d+)',
        ]
        for pat in patterns:
            m = re.search(pat, text, re.IGNORECASE)
            if m:
                num = m.group(1).strip()
                num = re.sub(r'[\s—–]+', '-', num)
                # Для ISO стандартов добавляем префикс
                if 'ISO' in pat:
                    return 'ISO ' + num
                return num
        return "unknown"

    # ================================================================
    # Поиск типа изделия
    # ================================================================
    def _find_product_name(self, text: str) -> str:
        text_lower = text.lower()
        if 'гайк' in text_lower:
            return "Гайка"
        if 'болт' in text_lower:
            return "Болт"
        if 'винт' in text_lower:
            return "Винт"
        if 'шпильк' in text_lower:
            return "Шпилька"
        if 'шайб' in text_lower:
            return "Шайба"
        return "Изделие"

    # ================================================================
    # Исправление кодировки (CP1252 -> Кириллица)
    # ================================================================
    def _fix_encoding(self, text: str) -> str:
        """Исправляет кириллицу, сохранённую в CP1252."""
        # Если текст уже содержит нормальную кириллицу — не трогаем
        if any('\u0410' <= ch <= '\u044F' for ch in text[:200]):
            return text
        # Пробуем перекодировать: Unicode CP1252 -> bytes -> CP1251 -> Unicode
        try:
            fixed = text.encode('cp1252').decode('cp1251')
            if any('\u0410' <= ch <= '\u044F' for ch in fixed[:200]):
                return fixed
        except (UnicodeEncodeError, UnicodeDecodeError):
            pass
        return text

    # ================================================================
    # Парсинг таблицы через текст get_text() — для landscape-таблиц
    # ================================================================
    def _try_parse_dimension_table(self, page_text: str) -> bool:
        """Парсит таблицу размеров из текста страницы (построчно)."""
        lines = [l.strip() for l in page_text.split('\n')]
        # Ищем маркер "Номинальный диаметр" или "Резьба D"
        start = None
        for i, line in enumerate(lines):
            low = line.lower()
            if ('оминальн' in line and 'диаметр' in low) or \
               ('езьб' in low and ('d' in low or 'D' in line)):
                start = i
                break
        if start is None:
            return False

        # Собираем диаметры (числа после маркера)
        diameters = []
        idx = start + 1
        while idx < len(lines):
            line = lines[idx].strip()
            clean = re.sub(r'[()а-яa-zА-ЯA-Z]', '', line, flags=re.IGNORECASE).strip()
            clean = re.sub(r'^[МмMm]\s*', '', clean).replace(',', '.')
            if re.match(r'^\d+(\.\d+)?$', clean) and clean:
                diameters.append(clean)
                idx += 1
            elif line == '' or 'езьб' in line.lower():
                idx += 1
            else:
                break
        if len(diameters) < 3:
            return False
        self.data.diameters = diameters
        n = len(diameters)

        # Парсим секции: заголовок + числа
        sections = self._parse_table_sections(lines, idx, n)
        self._assign_sections(sections, diameters)
        return True

    # ================================================================
    # Парсинг таблицы через bbox-координаты (для стандартных таблиц)
    # ================================================================
    def _try_parse_dimension_table_bbox(self, page_idx: int) -> bool:
        """Парсит таблицу размеров используя X,Y координаты текстовых элементов.
        Так мы точно привязываем мелкий шаг к правильному диаметру."""
        page = self._doc[page_idx]
        text = self._fix_encoding(page.get_text())

        # Проверяем, есть ли на этой странице таблица размеров
        if not ('оминальн' in text and 'диаметр' in text.lower()) and \
           not ('езьб' in text.lower() and ('d' in text.lower() or 'D' in text)):
            return False

        # Извлекаем все текстовые спаны с координатами
        spans = self._extract_spans(page)
        if not spans:
            return False

        # Группируем спаны по Y (строки) с допуском
        rows = self._group_by_y(spans, tolerance=6)

        # Ищем строку, содержащую диаметры (первый ряд числовых данных в таблице)
        # Это строка с "Номинальный диаметр" или первая строка после неё
        diameters, diam_x_positions = self._find_diameter_row(rows, spans)
        if not diameters:
            return False

        self.data.diameters = diameters
        logger.info(f"  Диаметры ({len(diameters)}): {diameters[:8]}...")

        # Ищем строки заголовков: "крупный", "мелкий", "Размер ... S", и т.д.
        self._extract_rows_by_headers(rows, diam_x_positions, diameters)

        return len(diameters) >= 3
        """Пытается найти и разобрать таблицу размеров на странице.
        Возвращает True если таблица найдена."""
        lines = page_text.split('\n')
        lines = [l.strip() for l in lines]

        # Ищем маркер "Номинальный диаметр" или "резьбы d" или "Резьба D"
        diameter_start = None
        for i, line in enumerate(lines):
            low = line.lower()
            if 'оминальн' in line and 'диаметр' in low:
                diameter_start = i
                break
            if 'езьб' in low and ('d' in low or 'D' in line):
                diameter_start = i
                break

        if diameter_start is None:
            return False

        # Собираем числа после маркера — это диаметры
        # Формат 1: числа по одному: "3", "4", "(14)", ...
        # Формат 2: с буквой М: "М1,6", "М2", "(М3,5)а", ...
        diameters = []
        idx = diameter_start + 1
        while idx < len(lines):
            line = lines[idx].strip()
            # Убираем скобки, буквы после скобок: (М3,5)а -> М3,5
            clean = re.sub(r'[()а-яa-z]', '', line, flags=re.IGNORECASE).strip()
            # Убираем "М" или "M" перед числом
            clean = re.sub(r'^[МмMm]\s*', '', clean)
            clean = clean.replace(',', '.')
            if re.match(r'^\d+(\.\d+)?$', clean) and clean:
                diameters.append(clean)
                idx += 1
            elif line == '' or 'езьбы' in line.lower() or 'езьба' in line.lower():
                idx += 1  # пропускаем пустые и "резьбы d"
            else:
                break  # текстовый маркер — конец диаметров

        if len(diameters) < 3:
            return False

        self.data.diameters = diameters
        n = len(diameters)  # количество столбцов таблицы

        # Теперь разбираем оставшиеся секции таблицы.
        # Каждая секция: текстовый заголовок, затем числа (по n штук).
        # Секции: крупный шаг, мелкий шаг, S, e, da_min, da_max, dw, m и т.д.
        sections = self._parse_table_sections(lines, idx, n)

        # Распределяем секции по полям
        self._assign_sections(sections, diameters)

        return True

    def _parse_table_sections(self, lines, start_idx, expected_count):
        """Парсит секции таблицы: заголовок + числа."""
        sections = []
        idx = start_idx
        current_header = ""
        current_nums = []

        while idx < len(lines):
            line = lines[idx].strip()
            if not line:
                idx += 1
                continue

            # Пробуем распарсить как число
            clean = line.replace(',', '.').replace('—', '').replace('−', '')
            # Может быть "23,9 26,8" (два числа на одной строке)
            nums_in_line = re.findall(r'\d+(?:\.\d+)?', clean)

            if nums_in_line and not re.search(r'[а-яА-ЯёЁa-zA-Z]{2,}', line):
                # Строка с числами
                current_nums.extend(nums_in_line)
            else:
                # Текстовая строка — потенциально новая секция
                # Сохраняем предыдущую секцию если есть данные
                if current_header and current_nums:
                    sections.append((current_header, current_nums))
                    current_nums = []
                    current_header = ""

                # Проверяем, не конец ли таблицы
                if 'римечан' in line or ('ример' in line.lower() and 'услов' in line.lower()):
                    break

                # Начинаем новый заголовок
                if current_header:
                    current_header = current_header + ' ' + line
                else:
                    current_header = line
            idx += 1

        # Последняя секция
        if current_header and current_nums:
            sections.append((current_header, current_nums))

        return sections

    def _assign_sections(self, sections, diameters):
        """Распределяет секции по полям ParsedGostData."""
        n = len(diameters)

        for header, nums in sections:
            h = header.lower()
            logger.info(f"  Секция: '{header}' -> {len(nums)} чисел")

            if 'крупн' in h:
                self._map_pitches_coarse(diameters, nums)
            elif 'P' in header and len(nums) == n and 'крупн' not in h:
                # ISO формат: секция "P b" = шаг резьбы (крупный)
                self._map_pitches_coarse(diameters, nums)
            elif 'мелк' in h:
                self._map_pitches_fine(diameters, nums)
            elif 'ключ' in h or ('размер' in h and 's' in h.lower()):
                self._map_to_dict(diameters, nums, self.data.wrench_sizes)
            elif 'описанн' in h or ('е' in h and 'менее' in h and 'dа' not in h and 'dw' not in h):
                self._map_to_dict_float(diameters, nums, self.data.e_min_values)
            elif 'dа' in h or 'da' in h.lower():
                if 'более' in h:
                    self._map_to_dict_float(diameters, nums, self.data.da_max_values)
                elif 'менее' in h:
                    self._map_to_dict_float(diameters, nums, self.data.da_min_values)
            elif 'dw' in h:
                self._map_to_dict_float(diameters, nums, self.data.dw_min_values)
            elif 'ысот' in h or ('m' in h and len(h) < 20):
                self._map_to_dict_float(diameters, nums, self.data.m_values)
            elif 'более' in h and 'm' in h:
                self._map_to_dict_float(diameters, nums, self.data.m_max_values)
            elif 'менее' in h and 'm' in h:
                self._map_to_dict_float(diameters, nums, self.data.m_min_values)
            elif 'более' in h and 's' in h.lower():
                self._map_to_dict_float(diameters, nums, self.data.s_nom_values)
            elif 'менее' in h and 's' in h.lower():
                self._map_to_dict_float(diameters, nums, self.data.s_min_values)

    def _extract_spans(self, page):
        """Извлекает все текстовые спаны с координатами."""
        spans = []
        for block in page.get_text("dict")["blocks"]:
            if "lines" not in block:
                continue
            for line in block["lines"]:
                for span in line["spans"]:
                    t = span['text'].strip()
                    if t:
                        t = self._fix_encoding(t)
                        spans.append({
                            'text': t,
                            'x0': span['bbox'][0],
                            'x1': span['bbox'][2],
                            'cx': (span['bbox'][0] + span['bbox'][2]) / 2,
                            'cy': (span['bbox'][1] + span['bbox'][3]) / 2,
                        })
        return spans

    def _group_by_y(self, spans, tolerance=6):
        """Группирует спаны по Y-координате (строки)."""
        from collections import defaultdict
        rows = defaultdict(list)
        for s in spans:
            y_key = round(s['cy'] / tolerance) * tolerance
            rows[y_key].append(s)
        # Сортируем элементы каждой строки по X
        for y_key in rows:
            rows[y_key].sort(key=lambda s: s['x0'])
        return rows

    def _find_diameter_row(self, rows, spans):
        """Находит строку с диаметрами и возвращает (diameters, x_positions)."""
        # Находим Y-координату заголовка "Номинальный диаметр" или "Резьба D"
        header_y = None
        for s in spans:
            if 'оминальн' in s['text'] and 'диаметр' in s['text'].lower():
                header_y = s['cy']
                break
            if 'езьб' in s['text'].lower() and ('D' in s['text'] or 'd' in s['text']):
                header_y = s['cy']
                break
        if header_y is None:
            return ([], {})

        # Ищем числовую строку, ближайшую к заголовку (в пределах 100 пикс.)
        best = ([], {})
        for y_key in sorted(rows.keys()):
            # Проверяем близость к заголовку
            if abs(y_key - header_y) > 100:
                continue
            items = rows[y_key]
            nums = []
            x_pos = {}
            for s in items:
                clean = re.sub(r'[()а-яa-zА-ЯA-Z]', '', s['text']).strip()
                clean = clean.replace(',', '.')
                if re.match(r'^\d+(\.\d+)?$', clean):
                    val = float(clean)
                    if 1 <= val <= 200:
                        d_str = clean.rstrip('0').rstrip('.') if '.' in clean else clean
                        nums.append(d_str)
                        x_pos[d_str] = s['cx']
            if len(nums) >= 5:
                vals = [float(n) for n in nums]
                is_increasing = all(vals[i] < vals[i+1] for i in range(len(vals)-1))
                if is_increasing and len(nums) > len(best[0]):
                    best = (nums, x_pos)
        return best

    def _extract_rows_by_headers(self, rows, diam_x_positions, diameters):
        """Для каждой строки таблицы определяет заголовок и привязывает числа к диаметрам."""
        header_map = {
            'крупн': 'coarse',
            'P b': 'coarse',
            'P ': 'coarse',
            'мелк': 'fine',
            'ключ': 'wrench',
            'описанн': 'e_min',
            'dw': 'dw_min',
            'ысот': 'm',
        }

        for y_key in sorted(rows.keys()):
            items = rows[y_key]
            # Собираем текст строки
            texts = [s['text'] for s in items]
            full_text = ' '.join(texts)

            # Определяем тип строки по заголовку
            row_type = None
            for keyword, rtype in header_map.items():
                if keyword in full_text:
                    row_type = rtype
                    break

            if not row_type:
                continue

            # Привязываем числовые значения к ближайшему диаметру по X
            for s in items:
                clean = s['text'].replace(',', '.').replace('—', '').replace('−', '').strip()
                if not re.match(r'^-?\d+(\.\d+)?$', clean):
                    continue
                # Ищем ближайший диаметр по X
                best_d = None
                best_dist = float('inf')
                for d, dx in diam_x_positions.items():
                    dist = abs(s['cx'] - dx)
                    if dist < best_dist:
                        best_dist = dist
                        best_d = d

                if best_d is None or best_dist > 30:
                    continue

                val = clean
                if row_type == 'coarse':
                    self.data.coarse_pitches[best_d] = val
                elif row_type == 'fine':
                    if best_d not in self.data.fine_pitches:
                        self.data.fine_pitches[best_d] = []
                    self.data.fine_pitches[best_d].append(val)
                elif row_type == 'wrench':
                    self.data.wrench_sizes[best_d] = val
                elif row_type == 'e_min':
                    try: self.data.e_min_values[best_d] = float(val)
                    except: pass
                elif row_type == 'dw_min':
                    try: self.data.dw_min_values[best_d] = float(val)
                    except: pass
                elif row_type == 'm':
                    try: self.data.m_values[best_d] = float(val)
                    except: pass

    def _fix_fine_pitches_via_bbox(self):
        """Уточняет мелкие шаги через pdftotext -layout.
        Использует позиции столбцов для точной привязки мелких шагов к диаметрам."""
        if not self.data.diameters:
            return

        # Путь к pdftotext
        from modules.config import POPPLER_PATH
        pdftotext = os.path.join(POPPLER_PATH, 'pdftotext.exe') if POPPLER_PATH else 'pdftotext'
        if not os.path.exists(pdftotext):
            logger.warning("pdftotext не найден, пропускаем уточнение мелких шагов")
            return

        # Запускаем pdftotext -layout на весь PDF
        import subprocess
        pdf_path = self._pdf_path
        result = subprocess.run(
            [pdftotext, '-layout', pdf_path, '-'],
            capture_output=True, text=True, encoding='utf-8', errors='replace'
        )
        if result.returncode != 0:
            return

        layout_text = result.stdout
        lines = layout_text.split('\n')

        # Ищем строку с диаметрами (числа 3, 4, 5, ... 48 в одну строку)
        diam_line_idx = None
        diam_positions = {}  # d -> X позиция (индекс символа)

        for i, line in enumerate(lines):
            # Ищем строку содержащую наши диаметры
            nums_found = 0
            for d in self.data.diameters[:5]:
                # Ищем число d как отдельное слово
                pattern = r'(?<!\d)' + re.escape(d.replace('.', ',')) + r'(?!\d)'
                if re.search(pattern, line):
                    nums_found += 1
                pattern2 = r'(?<!\d)' + re.escape(d) + r'(?!\d)'
                if re.search(pattern2, line):
                    nums_found += 1
            if nums_found >= 3:
                diam_line_idx = i
                # Определяем X-позиции каждого диаметра в строке
                for d in self.data.diameters:
                    d_comma = d.replace('.', ',')
                    for pat in [d_comma, d]:
                        for m in re.finditer(r'(?<!\d)' + re.escape(pat) + r'(?!\d)', line):
                            diam_positions[d] = m.start()
                            break
                        if d in diam_positions:
                            break
                break

        if not diam_positions:
            return

        # Ищем строку "мелкий" в ±10 строк от диаметров
        self.data.fine_pitches = {}
        for i in range(max(0, diam_line_idx - 10), min(len(lines), diam_line_idx + 10)):
            if 'мелк' in lines[i].lower():
                fine_line = lines[i]
                # Извлекаем все числа с их X-позициями, привязываем к ближайшему диаметру
                for m in re.finditer(r'\d+[.,]?\d*', fine_line):
                    num_text = m.group().replace(',', '.')
                    num_x = m.start()
                    # Находим ближайший диаметр по X
                    best_d = None
                    best_dist = float('inf')
                    for d, dx in diam_positions.items():
                        dist = abs(num_x - dx)
                        if dist < best_dist:
                            best_dist = dist
                            best_d = d
                    if best_d and best_dist < 15:
                        if best_d not in self.data.fine_pitches:
                            self.data.fine_pitches[best_d] = []
                        self.data.fine_pitches[best_d].append(num_text)
                break

    # ================================================================
    # Маппинг данных
    # ================================================================
    def _map_pitches_coarse(self, diameters, nums):
        """Маппинг крупных шагов. Их может быть меньше чем диаметров
        (для больших диаметров крупный шаг не указан)."""
        n = len(diameters)
        if len(nums) <= n:
            for i, val in enumerate(nums):
                if i < n and val and val != '0':
                    self.data.coarse_pitches[diameters[i]] = val

    def _map_pitches_fine(self, diameters, nums):
        """Маппинг мелких шагов. Их значительно меньше."""
        # Мелкие шаги привязаны не ко всем диаметрам
        # Нужно определить, к каким диаметрам относятся значения
        # По структуре ГОСТ 15524-70: мелкий шаг начинается с d=8
        n = len(diameters)
        if len(nums) < n:
            # Мелких шагов меньше — нужно найти соответствие
            # Ищем первый диаметр >= 8 (обычно мелкий шаг начинается с 8мм)
            start = 0
            for i, d in enumerate(diameters):
                if float(d) >= 8:
                    start = i
                    break
            for i, val in enumerate(nums):
                if start + i < n:
                    d = diameters[start + i]
                    if d not in self.data.fine_pitches:
                        self.data.fine_pitches[d] = []
                    self.data.fine_pitches[d].append(val)
        else:
            # Мелких шагов столько же сколько диаметров
            for i, val in enumerate(nums):
                if i < n:
                    d = diameters[i]
                    if d not in self.data.fine_pitches:
                        self.data.fine_pitches[d] = []
                    self.data.fine_pitches[d].append(val)

    def _map_to_dict(self, diameters, nums, target_dict):
        """Маппинг чисел к диаметрам (строковые значения)."""
        for i, val in enumerate(nums):
            if i < len(diameters):
                target_dict[diameters[i]] = val

    def _map_to_dict_float(self, diameters, nums, target_dict):
        """Маппинг чисел к диаметрам (float значения)."""
        for i, val in enumerate(nums):
            if i < len(diameters):
                try:
                    target_dict[diameters[i]] = float(val)
                except ValueError:
                    pass

    # ================================================================
    # Поиск примеров обозначений
    # ================================================================
    def _find_designation_examples(self, text: str):
        """Ищет примеры обозначений в тексте."""
        patterns = [
            r'(Гайка\s+\S+.*?ГОСТ\s+\S+)',
            r'(Болт\s+\S+.*?ГОСТ\s+\S+)',
            r'(Винт\s+\S+.*?ГОСТ\s+\S+)',
        ]
        for pat in patterns:
            for m in re.finditer(pat, text):
                example = m.group(1).strip()
                if len(example) < 200:
                    self.data.designation_examples.append(example)

    # ================================================================
    # Сводка
    # ================================================================
    def get_summary(self) -> str:
        d = self.data
        lines = [
            f"ГОСТ: {d.gost_number}",
            f"Изделие: {d.product_name}",
            f"Диаметры ({len(d.diameters)}): {', '.join(d.diameters[:10])}{'...' if len(d.diameters) > 10 else ''}",
            f"Крупный шаг ({len(d.coarse_pitches)}): {dict(list(d.coarse_pitches.items())[:5])}",
            f"Мелкий шаг ({len(d.fine_pitches)}): {dict(list(d.fine_pitches.items())[:5])}",
            f"Размер S ({len(d.wrench_sizes)}): {dict(list(d.wrench_sizes.items())[:5])}",
            f"Примеры обозначений: {len(d.designation_examples)}",
        ]
        for ex in d.designation_examples[:3]:
            lines.append(f"  -> {ex}")
        return '\n'.join(lines)
