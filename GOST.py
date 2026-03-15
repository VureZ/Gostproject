# -*- coding: utf-8 -*-
"""
GOST Processor - Edinaya tochka vhoda.
Zapusk: python GOST.py  ili  start.bat
"""

import os
import sys
import traceback

os.environ['FLAGS_use_mkldnn'] = '0'
os.environ['FLAGS_use_onednn'] = '0'
os.environ['PADDLE_USE_ONEDNN'] = '0'

import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    stream=sys.stderr, force=True
)


# ============================================================
# Komanda 1: PDF -> Polnyj pajplajn
# ============================================================
def cmd_pipeline():
    pdfs = sorted([f for f in os.listdir('data')
                   if f.endswith('.pdf') and f != 'Chat.pdf'])
    if not pdfs:
        print("Net PDF v papke data/")
        return
    print(f"\nPDF fajly:")
    for i, f in enumerate(pdfs):
        print(f"  {i+1}. {f}")
    choice = input("Nomer: ").strip()
    try:
        pdf_path = os.path.join('data', pdfs[int(choice) - 1])
    except (ValueError, IndexError):
        print("Neverno")
        return

    from modules.pipeline import GostPipeline
    pipe = GostPipeline()
    try:
        dc, pc = pipe.run_interactive(pdf_path)
        if dc > 0:
            print(f"\nItogo: {dc} oboznachenij, {pc} parametrov v SQL")
    except Exception as e:
        print(f"\nOshibka v pajplajne: {e}")
        traceback.print_exc()


# ============================================================
# Komanda 2: Statistika BD
# ============================================================
def cmd_stats():
    from modules.database import GostDatabase
    db = GostDatabase()
    if not db.connect():
        print("OSHIBKA: net SQL Server!")
        return
    try:
        total_d = db.get_designation_count()
        print(f"\n--- Statistika BD ---")
        print(f"Vsego oboznachenij: {total_d}")

        db.cursor.execute(
            "SELECT GOST_Number, COUNT(*) as cnt FROM ProductDesignations "
            "GROUP BY GOST_Number ORDER BY GOST_Number")
        rows = db.cursor.fetchall()
        if rows:
            print(f"\nPo GOSTam:")
            for r in rows:
                print(f"  {r[0]}: {r[1]} oboznachenij")

        db.cursor.execute("SELECT COUNT(*) FROM ProductParameters")
        print(f"\nVsego parametrov: {db.cursor.fetchone()[0]}")

        db.cursor.execute(
            "SELECT TOP 5 FullDesignation FROM ProductDesignations ORDER BY ID DESC")
        rows = db.cursor.fetchall()
        if rows:
            print(f"\nPoslednie 5:")
            for r in rows:
                print(f"  {r[0]}")
    finally:
        db.disconnect()


# ============================================================
# Komanda 3: OCR skanirovanie
# ============================================================
def cmd_ocr_scan():
    pdfs = sorted([f for f in os.listdir('data')
                   if f.endswith('.pdf') and f != 'Chat.pdf'])
    if not pdfs:
        print("Net PDF v papke data/")
        return
    print(f"\nPDF fajly:")
    for i, f in enumerate(pdfs):
        print(f"  {i+1}. {f}")
    choice = input("Nomer: ").strip()
    try:
        pdf_path = os.path.join('data', pdfs[int(choice) - 1])
    except (ValueError, IndexError):
        print("Neverno")
        return
    print(f"\nOCR: {pdf_path} (20-60 sek...)\n")
    _run_ocr(pdf_path)


def _run_ocr(pdf_path):
    from modules.pdf_processor import PDFProcessor
    from modules.ocr_engine import OCREngine
    from modules.table_parser import TableExtractor
    import numpy as np
    images = PDFProcessor(pdf_path).convert_to_images(dpi=300)
    print(f"Stranic: {len(images)}")
    ocr = OCREngine(language='ru', use_gpu=False)
    ext = TableExtractor(ocr_engine=ocr)
    pages = []
    for i, img in enumerate(images):
        print(f"  {i+1}/{len(images)}...", end=" ", flush=True)
        try:
            text = ext.get_full_page_text(np.array(img))
            pages.append(text)
            print(f"{len(text)} ch")
        except Exception as e:
            print(f"ERR: {e}")
            pages.append("")
    os.makedirs('output', exist_ok=True)
    fn = os.path.splitext(os.path.basename(pdf_path))[0]
    out = os.path.join('output', f'ocr_{fn}.txt')
    with open(out, 'w', encoding='utf-8') as f:
        for i, t in enumerate(pages):
            f.write(f"{'='*60}\nPAGE {i+1}\n{'='*60}\n{t}\n\n")
    print(f"\nSaved: {out}")


# ============================================================
# Menu
# ============================================================
def show_menu():
    print("\n" + "=" * 50)
    print("  GOST Processor")
    print("=" * 50)
    print("-" * 50)
    print("  1. PDF -> Polnyj pajplajn (avto-parsing)")
    print("  2. Statistika BD")
    print("  3. OCR skanirovanie PDF")
    print("  0. Vyhod")
    print("-" * 50)


def main():
    if '--stats' in sys.argv:
        cmd_stats()
        return

    while True:
        show_menu()
        c = input("Vybor: ").strip()
        if c == '1':
            cmd_pipeline()
        elif c == '2':
            cmd_stats()
        elif c == '3':
            cmd_ocr_scan()
        elif c == '0':
            print("Do svidaniya!")
            break
        else:
            print("Neizvestnyj punkt")


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f"\nKriticheskaya oshibka: {e}")
        traceback.print_exc()
        input("\nPress Enter to exit...")
