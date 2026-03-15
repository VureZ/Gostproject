"""
Файл конфигурации для GOST OCR Processor
"""

import os
import sys

# ==================== ПУТИ К ФАЙЛАМ ====================

# Определяем базовые директории
# При запуске из PyInstaller EXE: ресурсы в sys._MEIPASS, данные рядом с EXE
# При обычном запуске: всё в папке проекта
if getattr(sys, 'frozen', False):
    # PyInstaller EXE
    BUNDLE_DIR = sys._MEIPASS  # встроенные ресурсы (poppler, modules)
    BASE_DIR = os.path.dirname(sys.executable)  # папка с EXE (data, output)
    POPPLER_PATH = os.path.join(BUNDLE_DIR, 'poppler')
else:
    # Обычный Python
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    BUNDLE_DIR = BASE_DIR
    POPPLER_PATH = os.path.join(BASE_DIR, 'poppler', 'poppler-25.12.0', 'Library', 'bin')

PDF_INPUT_DIR = os.path.join(BASE_DIR, 'data')
OUTPUT_DIR = os.path.join(BASE_DIR, 'output')
TEMPLATES_DIR = os.path.join(BASE_DIR, 'templates')

# ==================== НАСТРОЙКИ SQL SERVER ====================

SQL_SERVER_CONFIG = {
    'server': 'HOME-PC',
    'database': 'GOST_Database',
    'preferred_drivers': [
        'ODBC Driver 17 for SQL Server',
        'ODBC Driver 18 for SQL Server',
        'SQL Server Native Client 11.0',
        'SQL Server',
    ],
    'trusted_connection': 'yes',
    'connection_timeout': 10,
}

def get_sql_connection_string():
    """Возвращает строку подключения к SQL Server."""
    import pyodbc
    available_drivers = pyodbc.drivers()
    
    selected_driver = None
    for preferred in SQL_SERVER_CONFIG['preferred_drivers']:
        if preferred in available_drivers:
            selected_driver = preferred
            break
    
    if not selected_driver:
        sql_drivers = [d for d in available_drivers if 'SQL Server' in d]
        selected_driver = sql_drivers[0] if sql_drivers else 'SQL Server'
    
    connection_string = (
        f"DRIVER={{{selected_driver}}};"
        f"SERVER={SQL_SERVER_CONFIG['server']};"
        f"DATABASE={SQL_SERVER_CONFIG['database']};"
        f"Trusted_Connection={SQL_SERVER_CONFIG['trusted_connection']};"
        f"Connection Timeout={SQL_SERVER_CONFIG['connection_timeout']};"
    )
    
    if 'ODBC Driver 17' in selected_driver or 'ODBC Driver 18' in selected_driver:
        connection_string += "TrustServerCertificate=yes;"
    
    return connection_string, selected_driver

_SQL_CONNECTION_STRING = None
_SQL_DRIVER_USED = None

def get_connection_string():
    global _SQL_CONNECTION_STRING, _SQL_DRIVER_USED
    if _SQL_CONNECTION_STRING is None:
        _SQL_CONNECTION_STRING, _SQL_DRIVER_USED = get_sql_connection_string()
    return _SQL_CONNECTION_STRING

def get_driver_name():
    global _SQL_DRIVER_USED
    if _SQL_DRIVER_USED is None:
        get_connection_string()
    return _SQL_DRIVER_USED

# ==================== НАСТРОЙКИ PADDLEOCR ====================

OCR_LANGUAGE = 'ru'
USE_ANGLE_CLASSIFICATION = True
USE_GPU = False
OCR_CONFIDENCE_THRESHOLD = 0.6

# ==================== НАСТРОЙКИ PDF ====================

PDF_DPI = 300
IMAGE_FORMAT = 'PNG'

# ==================== НАСТРОЙКИ ЛОГИРОВАНИЯ ====================

LOG_LEVEL = 'INFO'
LOG_FILE = os.path.join(BASE_DIR, 'app.log')

# ==================== СОЗДАНИЕ ПАПОК ====================

def create_directories():
    """Создает необходимые папки если их нет"""
    for d in [PDF_INPUT_DIR, OUTPUT_DIR, TEMPLATES_DIR]:
        os.makedirs(d, exist_ok=True)

if __name__ != '__main__':
    create_directories()
