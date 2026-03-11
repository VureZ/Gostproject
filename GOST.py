# -*- coding: utf-8 -*-
"""
GOST Processor - Edinaya tochka vhoda.
Zapusk: python GOST.py  ili  start.bat
"""

import os
import sys
import json
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
# Hardcoded GOST (vsegda dostupny)
# ============================================================
GOST_REGISTRY = {
    '10605': {
        'module': 'data.gost_10605_94',
        'spec_func': 'get_gost_10605_94',
        'params_func': 'get_parameters_10605_94',
        'name': 'GOST 10605-94 (Gajki shestigrannyje d>48mm)',
    },
    '4036': {
        'module': 'data.gost_iso_4036_2014',
        'spec_func': 'get_gost_iso_4036_2014',
        'params_func': 'get_parameters_iso_4036_2014',
        'name': 'ГОСТ ISO 4036-2014 (Гайки низкие без фаски тип 0)',
    },
    '15524': {
        'module': 'data.gost_15524_70',
        'spec_func': 'get_gost_15524_70',
        'params_func': 'get_parameters_15524_70',
        'name': 'ГОСТ 15524-70 (Гайки шестигранные высокие кл.А)',
    },
}

REGISTRY_JSON = os.path.join('data', 'registry.json')


def get_all_gosts():
    """Polnyj reestr: hardcoded + iz registry.json."""
    result = dict(GOST_REGISTRY)
    if os.path.exists(REGISTRY_JSON):
        try:
            with open(REGISTRY_JSON, 'r', encoding='utf-8') as f:
                extra = json.load(f)
            result.update(extra)
        except Exception:
            pass
    return result


def load_gost(key):
    """Zagruzit spec i parametry GOST po klyuchu."""
    registry = get_all_gosts()
    info = registry[key]
    mod = __import__(info['module'], fromlist=[info['spec_func']])
    spec = getattr(mod, info['spec_func'])()
    params = None
    pf = info.get('params_func')
    if pf:
        params = getattr(mod, pf)()
    return spec, params, info['name']


def select_gost():
    """Polzovatel vybiraet GOST iz spiska."""
    registry = get_all_gosts()
    keys = list(registry.keys())
    
    print("\nDostupnye GOST:")
    for i, k in enumerate(keys):
        print(f"  {i+1}. {registry[k]['name']}")
    
    choice = input("Vyberi nomer: ").strip()
    try:
        return keys[int(choice) - 1]
    except (ValueError, IndexError):
        print("Neverno")
        return None


# ============================================================
# Komanda 1: Sgenerirovat (odin GOST) -> SQL
# ============================================================
def cmd_generate_single():
    key = select_gost()
    if not key:
        return
    
    from modules.designation_generator import DesignationGenerator
    from modules.database import GostDatabase
    
    spec, params, name = load_gost(key)
    print(f"\n--- {name} ---")
    
    gen = DesignationGenerator(spec)
    designations = gen.generate_all()
    print(f"Sgenerrirovano: {len(designations)} oboznachenij")
    
    print("\nPrimery:")
    for d in designations[:5]:
        print(f"  {d['FullDesignation']}")
    if len(designations) > 10:
        print(f"  ...")
        print(f"  {designations[-1]['FullDesignation']}")
    
    ans = input(f"\nZapisat v SQL? (y/n): ").strip().lower()
    if ans != 'y':
        print("Otmeneno")
        return
    
    db = GostDatabase()
    if not db.connect():
        print("OSHIBKA: net SQL Server!")
        return
    try:
        dc = db.insert_designations(designations, clear_existing=True)
        print(f"Oboznachenij: {dc}")
        if params:
            pc = db.insert_parameters(params, clear_existing=True)
            print(f"Parametrov: {pc}")
        print("GOTOVO!")
    except Exception as e:
        print(f"Oshibka: {e}")
    finally:
        db.disconnect()
    _save_csv(spec, designations)


# ============================================================
# Komanda 2: Sgenerirovat VSE -> SQL
# ============================================================
def cmd_generate_all():
    from modules.designation_generator import DesignationGenerator
    from modules.database import GostDatabase
    
    registry = get_all_gosts()
    db = GostDatabase()
    if not db.connect():
        print("OSHIBKA: net SQL Server!")
        return
    
    total_d, total_p = 0, 0
    for key in registry:
        try:
            spec, params, name = load_gost(key)
            print(f"\n--- {name} ---")
            gen = DesignationGenerator(spec)
            designations = gen.generate_all()
            dc = db.insert_designations(designations, clear_existing=True)
            total_d += dc
            print(f"  Oboznachenij: {dc}")
            if params:
                pc = db.insert_parameters(params, clear_existing=True)
                total_p += pc
                print(f"  Parametrov: {pc}")
            _save_csv(spec, designations)
        except Exception as e:
            print(f"  Oshibka: {e}")
    
    db.disconnect()
    print(f"\n{'='*50}")
    print(f"ITOGO: {total_d} oboznachenij, {total_p} parametrov")


# ============================================================
# Komanda 3: Statistika
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
        registry = get_all_gosts()
        for key in registry:
            try:
                spec, _, name = load_gost(key)
                cnt = db.get_designation_count(spec.gost_number)
                print(f"  {name}: {cnt}")
            except Exception:
                pass
        db.cursor.execute("SELECT COUNT(*) FROM ProductParameters")
        print(f"Vsego parametrov: {db.cursor.fetchone()[0]}")
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
# Komanda 4: OCR
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
# Komanda 5: Dobavit novyj GOST (wizard)
# ============================================================
def cmd_add_gost():
    from modules.gost_wizard import run_wizard
    result = run_wizard()
    if result is None:
        return
    
    spec, designations = result
    
    ans = input(f"\nSrazu zapisat {len(designations)} oboznachenij v SQL? (y/n): ").strip().lower()
    if ans == 'y':
        from modules.database import GostDatabase
        db = GostDatabase()
        if db.connect():
            dc = db.insert_designations(designations, clear_existing=True)
            print(f"Zapisano: {dc}")
            db.disconnect()
        else:
            print("OSHIBKA: net SQL Server!")
    
    _save_csv(spec, designations)


# ============================================================
# Komanda 6: PDF -> Polnyj pajplajn
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
    dc, pc = pipe.run_interactive(pdf_path)
    if dc > 0:
        print(f"\nItogo: {dc} oboznachenij, {pc} parametrov v SQL")


# ============================================================
# Utility
# ============================================================
def _save_csv(spec, designations):
    os.makedirs('output', exist_ok=True)
    safe = spec.gost_number.replace(' ', '_').replace('-', '_')
    path = os.path.join('output', f'designations_{safe}.csv')
    with open(path, 'w', encoding='utf-8') as f:
        cols = ['GOST_Number','FullDesignation','ThreadSize',
                'MaterialGroup','Coating','SteelGrade',
                'ThreadDiameter','ThreadPitch']
        f.write(";".join(cols) + "\n")
        for d in designations:
            f.write(";".join([str(d.get(c,'')) for c in cols]) + "\n")
    print(f"CSV: {path}")


# ============================================================
# Menu
# ============================================================
def show_menu():
    print("\n" + "=" * 50)
    print("  GOST Processor")
    print("=" * 50)
    registry = get_all_gosts()
    print(f"  Zaregistrirovano GOST: {len(registry)}")
    print("-" * 50)
    print("  1. Sgenerirovat oboznacheniya (1 GOST) -> SQL")
    print("  2. Sgenerirovat VSE -> SQL")
    print("  3. Statistika BD")
    print("  4. OCR skanirovanie PDF")
    print("  5. Dobavit novyj GOST (master)")
    print("  6. PDF -> Полный пайплайн (авто)")
    print("  0. Vyhod")
    print("-" * 50)


def main():
    if '--generate-all' in sys.argv:
        cmd_generate_all()
        return
    if '--stats' in sys.argv:
        cmd_stats()
        return
    
    while True:
        show_menu()
        c = input("Vybor: ").strip()
        if c == '1':
            cmd_generate_single()
        elif c == '2':
            cmd_generate_all()
        elif c == '3':
            cmd_stats()
        elif c == '4':
            cmd_ocr_scan()
        elif c == '5':
            cmd_add_gost()
        elif c == '6':
            cmd_pipeline()
        elif c == '0':
            print("Do svidaniya!")
            break
        else:
            print("Neizvestnyj punkt")


if __name__ == '__main__':
    main()
