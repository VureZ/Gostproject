# -*- coding: utf-8 -*-
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from modules.database import GostDatabase

db = GostDatabase()
ok = db.connect()
print(f"SQL connected: {ok}")

if ok:
    # Проверяем что таблицы существуют
    try:
        db.cursor.execute("SELECT COUNT(*) FROM ProductDesignations")
        cnt = db.cursor.fetchone()[0]
        print(f"ProductDesignations: {cnt} записей")
    except Exception as e:
        print(f"Ошибка ProductDesignations: {e}")

    try:
        db.cursor.execute("SELECT COUNT(*) FROM ProductParameters")
        cnt = db.cursor.fetchone()[0]
        print(f"ProductParameters: {cnt} записей")
    except Exception as e:
        print(f"Ошибка ProductParameters: {e}")

    db.disconnect()
