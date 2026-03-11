"""
Модуль для извлечения таблиц из изображений ГОСТ/ОСТ документов.
Использует PaddleOCR для распознавания текста и умную группировку
по координатам для восстановления структуры таблиц.
"""

import re
import cv2
import numpy as np
from typing import List, Dict, Tuple, Optional, Any
from dataclasses import dataclass, field
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class Table:
    """Структурированная таблица"""
    headers: List[str] = field(default_factory=list)
    rows: List[List[str]] = field(default_factory=list)
    bbox: Optional[List[int]] = None
    page_number: int = 0
    table_name: str = ""


class TableExtractor:
    """
    Извлекает таблицы из изображений страниц ГОСТ.
    
    Подход: OCR всего текста → группировка по строкам → 
    определение столбцов → восстановление таблицы.
    """
    
    def __init__(self, ocr_engine=None):
        self.ocr_engine = ocr_engine
    
    def extract_tables_from_image(self, image: np.ndarray, 
                                  page_num: int = 0) -> List[Table]:
        """
        Главный метод: извлекает все таблицы со страницы.
        
        Args:
            image: изображение страницы (numpy array BGR)
            page_num: номер страницы
        Returns:
            список найденных таблиц
        """
        if self.ocr_engine is None:
            logger.error("OCR движок не задан")
            return []
        
        # Шаг 1: Распознаём весь текст на странице
        text_items = self.ocr_engine.recognize_text(image)
        if not text_items:
            logger.warning(f"Страница {page_num}: текст не распознан")
            return []
        
        logger.info(f"Страница {page_num}: распознано {len(text_items)} элементов")
        
        # Шаг 2: Группируем текст по строкам
        rows = self._group_into_rows(text_items)
        
        # Шаг 3: Находим области с табличной структурой
        table_regions = self._find_table_regions(rows)
        
        # Шаг 4: Для каждого региона строим таблицу
        tables = []
        for region in table_regions:
            table = self._build_table(region, page_num)
            if table and len(table.rows) >= 1:
                tables.append(table)
        
        logger.info(f"Страница {page_num}: найдено таблиц: {len(tables)}")
        return tables
    
    def _group_into_rows(self, text_items: List[Dict], 
                         threshold: int = 15) -> List[List[Dict]]:
        """
        Группирует текстовые элементы по строкам на основе Y-координат.
        
        Args:
            text_items: список элементов от OCR [{text, bbox, confidence}]
            threshold: допуск по Y для объединения в одну строку (пикс.)
        Returns:
            список строк, каждая строка = список элементов
        """
        if not text_items:
            return []
        
        # Вычисляем центр Y для каждого элемента
        items_with_y = []
        for item in text_items:
            bbox = item['bbox']
            cy = (bbox[0][1] + bbox[2][1]) / 2  # центр по Y
            cx = (bbox[0][0] + bbox[2][0]) / 2  # центр по X
            items_with_y.append({**item, '_cy': cy, '_cx': cx})
        
        # Сортируем по Y
        items_with_y.sort(key=lambda x: x['_cy'])
        
        # Группируем
        rows = []
        current_row = [items_with_y[0]]
        current_y = items_with_y[0]['_cy']
        
        for item in items_with_y[1:]:
            if abs(item['_cy'] - current_y) <= threshold:
                current_row.append(item)
            else:
                # Сортируем строку по X (слева направо)
                current_row.sort(key=lambda x: x['_cx'])
                rows.append(current_row)
                current_row = [item]
                current_y = item['_cy']
        
        # Последняя строка
        if current_row:
            current_row.sort(key=lambda x: x['_cx'])
            rows.append(current_row)
        
        return rows
    
    def _find_table_regions(self, rows: List[List[Dict]]) -> List[List[List[Dict]]]:
        """
        Находит непрерывные области с табличной структурой.
        
        Критерий: несколько последовательных строк с >= 3 элементами
        и примерно одинаковым числом столбцов.
        """
        if len(rows) < 2:
            return []
        
        regions = []
        current_region = []
        
        for row in rows:
            col_count = len(row)
            
            if col_count >= 3:
                # Строка с >= 3 элементами — потенциально табличная
                if current_region:
                    prev_count = len(current_region[-1])
                    # Допускаем разницу в ±2 столбца
                    if abs(col_count - prev_count) <= 2:
                        current_region.append(row)
                    else:
                        # Разрыв: сохраняем предыдущий регион если >= 3 строк
                        if len(current_region) >= 3:
                            regions.append(current_region)
                        current_region = [row]
                else:
                    current_region = [row]
            else:
                # Мало элементов — конец табличной области
                if len(current_region) >= 3:
                    regions.append(current_region)
                current_region = []
        
        # Последний регион
        if len(current_region) >= 3:
            regions.append(current_region)
        
        logger.info(f"Найдено табличных регионов: {len(regions)}")
        return regions
    
    def _build_table(self, region: List[List[Dict]], 
                     page_num: int) -> Optional[Table]:
        """
        Строит объект Table из региона строк.
        Определяет сетку столбцов и выравнивает данные.
        """
        if not region:
            return None
        
        # Определяем позиции столбцов по всем строкам региона
        col_positions = self._detect_columns(region)
        
        if len(col_positions) < 2:
            return None
        
        # Заполняем таблицу
        all_rows = []
        for row_items in region:
            row_texts = self._assign_to_columns(row_items, col_positions)
            all_rows.append(row_texts)
        
        # Первая строка = заголовки (если похожа на заголовок)
        headers = all_rows[0] if all_rows else []
        data_rows = all_rows[1:] if len(all_rows) > 1 else []
        
        return Table(
            headers=headers,
            rows=data_rows,
            page_number=page_num
        )
    
    def _detect_columns(self, region: List[List[Dict]]) -> List[float]:
        """
        Определяет позиции столбцов по X-координатам всех элементов.
        Кластеризует X-координаты центров элементов.
        """
        all_cx = []
        for row in region:
            for item in row:
                all_cx.append(item['_cx'])
        
        if not all_cx:
            return []
        
        # Простая кластеризация: сортируем и группируем близкие значения
        all_cx.sort()
        clusters = []
        current_cluster = [all_cx[0]]
        
        # Порог: элементы ближе 30 пикс. считаются одним столбцом
        col_threshold = 30
        
        for cx in all_cx[1:]:
            if cx - current_cluster[-1] <= col_threshold:
                current_cluster.append(cx)
            else:
                clusters.append(sum(current_cluster) / len(current_cluster))
                current_cluster = [cx]
        if current_cluster:
            clusters.append(sum(current_cluster) / len(current_cluster))
        
        return clusters
    
    def _assign_to_columns(self, row_items: List[Dict], 
                           col_positions: List[float]) -> List[str]:
        """
        Назначает каждый элемент строки ближайшему столбцу.
        Возвращает список текстов по столбцам.
        """
        result = [''] * len(col_positions)
        
        for item in row_items:
            cx = item['_cx']
            # Находим ближайший столбец
            min_dist = float('inf')
            best_col = 0
            for i, col_x in enumerate(col_positions):
                dist = abs(cx - col_x)
                if dist < min_dist:
                    min_dist = dist
                    best_col = i
            
            # Если ячейка уже заполнена — добавляем через пробел
            if result[best_col]:
                result[best_col] += ' ' + item['text']
            else:
                result[best_col] = item['text']
        
        return result
    
    def get_full_page_text(self, image: np.ndarray) -> str:
        """
        Извлекает весь текст со страницы в порядке чтения.
        Используется для поиска шаблона обозначения и другого текста.
        """
        if self.ocr_engine is None:
            return ""
        
        text_items = self.ocr_engine.recognize_text(image)
        if not text_items:
            return ""
        
        rows = self._group_into_rows(text_items, threshold=15)
        
        lines = []
        for row in rows:
            line = ' '.join(item['text'] for item in row)
            lines.append(line)
        
        return '\n'.join(lines)
