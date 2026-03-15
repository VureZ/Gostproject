"""
Универсальный модуль извлечения таблиц из PDF документов ГОСТ/ОСТ.
Использует PyMuPDF (для текстовых PDF) и PaddleOCR (для отсканированных).

ПРИМЕЧАНИЕ: Этот модуль — альтернативный подход. 
Основной подход — через GOST.py -> table_parser.py (OCR).
"""

import os
import re
import logging
import numpy as np
from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass, field
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Остальной код модуля пока не используется.
# Будет обновлён на Этапе 2.
