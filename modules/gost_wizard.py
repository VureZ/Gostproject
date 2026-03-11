# -*- coding: utf-8 -*-
"""
Interaktivnyj master dobavleniya novogo GOST.
Poshagovyj vvod dannyh cherez konsol, bez redaktirovaniya koda.

Sozdayot fajl data/gost_XXXXX.py i registriruet v sisteme.
"""

import os
import re
import json

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))), 'data')

# Fajl s reestrom vseh GOST (vmesto hardcode v GOST.py)
REGISTRY_FILE = os.path.join(DATA_DIR, 'registry.json')


def _ask(prompt, default=""):
    """Prosit polzovatelya vvesti znachenie."""
    if default:
        s = input(f"  {prompt} [{default}]: ").strip()
        return s if s else default
    else:
        s = input(f"  {prompt}: ").strip()
        return s


def _ask_list(prompt, example=""):
    """Prosit vvesti spisok cherez zapyatuyu."""
    hint = f" (primer: {example})" if example else ""
    s = input(f"  {prompt}{hint}: ").strip()
    if not s:
        return []
    # Razdelyaem po zapyatoj ili probelu
    items = re.split(r'[,;\s]+', s)
    return [x.strip() for x in items if x.strip()]


def _ask_dict(prompt, key_desc, val_desc, example=""):
    """Prosit vvesti pary klyuch=znachenie."""
    hint = f"\n    Primer: {example}" if example else ""
    print(f"  {prompt}{hint}")
    print(f"    Format: {key_desc}={val_desc} (po odnomu na stroku, pustaya stroka = konec)")
    result = {}
    while True:
        s = input("    > ").strip()
        if not s:
            break
        if '=' in s:
            k, v = s.split('=', 1)
            result[k.strip()] = v.strip()
        else:
            result[s] = ""
    return result


def load_registry():
    """Zagruzhaem reestr GOST iz JSON."""
    if os.path.exists(REGISTRY_FILE):
        with open(REGISTRY_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


def save_registry(registry):
    """Sohranyaem reestr GOST v JSON."""
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(REGISTRY_FILE, 'w', encoding='utf-8') as f:
        json.dump(registry, f, ensure_ascii=False, indent=2)


def run_wizard():
    """
    Glavnyj master dobavleniya GOST.
    Poshagovyj vvod vseh dannyh.
    """
    print("\n" + "=" * 55)
    print("  MASTER DOBAVLENIYA NOVOGO GOST")
    print("=" * 55)
    print("  Otvet'te na voprosy poshaagovo.")
    print("  Pustoj vvod = propusk (mozhno dopolnit potom).")
    print("=" * 55)
    
    # --- Shag 1: Osnovnye dannye ---
    print("\n[Shag 1/7] Osnovnye dannye")
    print("-" * 40)
    
    gost_number = _ask("Nomer GOST (naprimer: 10605-94 ili ISO 4035-2014)")
    if not gost_number:
        print("Nomer GOST obyazatelen! Otmena.")
        return None
    
    product_name = _ask("Nazvanie izdeliya (naprimer: Gajka, Bolt, Shpilka)", "Gajka")
    description = _ask("Opisanie (naprimer: Gajki shestigrannyje d>48mm)", "")
    
    # --- Shag 2: Diametry ---
    print("\n[Shag 2/7] Diametry rezby")
    print("-" * 40)
    diameters = _ask_list(
        "Vvedite diametry cherez zapyatuyu",
        "52, 56, 64, 72, 80, 90, 100"
    )
    if not diameters:
        print("Diametry obyazatelny! Otmena.")
        return None
    print(f"    Prinyato: {diameters}")
    
    # --- Shag 3: Shagi rezby ---
    print("\n[Shag 3/7] Shagi rezby")
    print("-" * 40)
    
    print("  Krupnyj shag (ne ukazyvaetsya v oboznachenii):")
    print("  Format: diametr=shag (naprimer: 52=5.0, 56=5.5)")
    print("  Esli u vseh odinkovyj shag, vvedite: all=5.0")
    print("  Pustaya stroka = propustit")
    coarse = {}
    while True:
        s = input("    > ").strip()
        if not s:
            break
        if '=' in s:
            k, v = s.split('=', 1)
            k = k.strip()
            v = v.strip()
            if k == 'all':
                for d in diameters:
                    coarse[d] = v
            else:
                coarse[k] = v
    if coarse:
        print(f"    Krupnyj shag: {coarse}")
    
    print("\n  Melkij shag (ukazyvaetsya v oboznachenii cherez 'x'):")
    print("  Format: diametr=shag1,shag2 (naprimer: 72=4.0,6.0)")
    print("  Pustaya stroka = propustit")
    fine = {}
    while True:
        s = input("    > ").strip()
        if not s:
            break
        if '=' in s:
            k, v = s.split('=', 1)
            pitches = [p.strip() for p in v.split(',') if p.strip()]
            fine[k.strip()] = pitches
    if fine:
        print(f"    Melkij shag: {fine}")
    
    # --- Shag 4: Materialy ---
    print("\n[Shag 4/7] Gruppy materialov")
    print("-" * 40)
    print("  Vvedite kody grupp i tip materiala:")
    print("  Format: kod=carbon ili kod=stainless")
    print("  Primer: 05=carbon ili A2-035=stainless")
    print("  Pustaya stroka = konec")
    groups = {}
    while True:
        s = input("    > ").strip()
        if not s:
            break
        if '=' in s:
            k, v = s.split('=', 1)
            v = v.strip().lower()
            if v not in ('carbon', 'stainless'):
                print("    Tip dolzhen byt: carbon ili stainless")
                continue
            groups[k.strip()] = v
    if groups:
        print(f"    Gruppy: {groups}")
    
    # --- Shag 5: Marki stali ---
    print("\n[Shag 5/7] Marki stali (dlya nerzhaveyuschih grupp)")
    print("-" * 40)
    stainless_groups = [k for k, v in groups.items() if v == 'stainless']
    grades = {}
    if stainless_groups:
        print(f"  Nerzhaveyuschie gruppy: {stainless_groups}")
        print("  Format: gruppa=marka1,marka2")
        print("  Primer: 21=12X18H9T,12X18H10T")
        for sg in stainless_groups:
            s = input(f"    Marki dlya gruppy {sg}: ").strip()
            if s:
                grades[sg] = [x.strip() for x in s.split(',') if x.strip()]
    else:
        print("  Net nerzhaveyuschih grupp - propuskayem")
    
    # --- Shag 6: Pokrytiya ---
    print("\n[Shag 6/7] Pokrytiya")
    print("-" * 40)
    print("  Format: kod=opisanie")
    print("  Primer: 019=Zn hrom 9mkm")
    print("  Pustaya stroka = bez pokrytij")
    coatings = {}
    while True:
        s = input("    > ").strip()
        if not s:
            break
        if '=' in s:
            k, v = s.split('=', 1)
            coatings[k.strip()] = v.strip()
        else:
            coatings[s] = ""
    if coatings:
        print(f"    Pokrytiya: {coatings}")
    
    # --- Shag 7: Format oboznacheniya ---
    print("\n[Shag 7/7] Format oboznacheniya")
    print("-" * 40)
    print("  Vyberi format:")
    print("  1. Standart: Izdelie M{d}.{gruppa}[.{pokrytie}] GOST {nomer}")
    print("     Primer:   Gajka M 56.05.019 GOST 10605-94")
    print("  2. ISO:      Izdelie GOST {nomer} - M{d}-{gruppa}")
    print("     Primer:   Gajka ... GOST ISO 4035-2014 - M12-05")
    print("  3. Svoj format (dlya opytnyh)")
    
    fmt_choice = _ask("Format", "1")
    
    format_coarse = ""
    format_fine = ""
    
    if fmt_choice == '2':
        format_coarse = "{product} GOST {gost} - M{diameter}-{group}"
        format_fine = "{product} GOST {gost} - M{diameter}x{pitch}-{group}"
    elif fmt_choice == '3':
        print("  Dostupnye peremennye:")
        print("    {product}, {gost}, {diameter}, {pitch},")
        print("    {group}, {steel_grade}, {coating}")
        format_coarse = _ask("Format (krupnyj shag)")
        format_fine = _ask("Format (melkij shag)")
    
    # --- Itogovaya svodka ---
    print("\n" + "=" * 55)
    print("  SVODKA")
    print("=" * 55)
    print(f"  GOST:        {gost_number}")
    print(f"  Izdelie:     {product_name}")
    print(f"  Diametry:    {', '.join(diameters)}")
    print(f"  Krupn. shag: {len(coarse)} zapisej")
    print(f"  Melk. shag:  {len(fine)} zapisej")
    print(f"  Gruppy mat.: {list(groups.keys())}")
    print(f"  Pokrytiya:   {list(coatings.keys()) if coatings else 'net'}")
    
    # Podschet kombinacij
    from modules.designation_generator import GostSpec, DesignationGenerator
    spec = GostSpec()
    spec.gost_number = gost_number
    spec.product_name = product_name
    spec.diameters = diameters
    spec.coarse_pitches = coarse
    spec.fine_pitches = fine
    spec.material_groups = groups
    spec.steel_grades = grades
    spec.coatings = coatings
    spec.format_coarse = format_coarse
    spec.format_fine = format_fine
    
    gen = DesignationGenerator(spec)
    designations = gen.generate_all()
    
    print(f"\n  Budet sgenerrirovano: {len(designations)} oboznachenij")
    if designations:
        print(f"  Primer: {designations[0]['FullDesignation']}")
        if len(designations) > 1:
            print(f"  Primer: {designations[-1]['FullDesignation']}")
    
    ans = input("\n  Sokhranit? (y/n): ").strip().lower()
    if ans != 'y':
        print("  Otmeneno.")
        return None
    
    # --- Sohranyaem fajl ---
    _save_gost_file(gost_number, product_name, description,
                    diameters, coarse, fine, groups, grades, coatings,
                    format_coarse, format_fine)
    
    # --- Registriruem v reestre ---
    _register_gost(gost_number, product_name, description)
    
    print(f"\n  GOST {gost_number} uspeshno dobavlen!")
    print(f"  Teper mozhno vybrat ego v menu (punkt 1 ili 2)")
    
    return spec, designations


def _make_safe_name(gost_number):
    """Prevraschaem nomer GOST v bezopasnoe imya fajla."""
    safe = gost_number.lower()
    safe = re.sub(r'[^a-z0-9]+', '_', safe)
    safe = safe.strip('_')
    return safe


def _save_gost_file(gost_number, product_name, description,
                    diameters, coarse, fine, groups, grades, coatings,
                    format_coarse, format_fine):
    """Sozdayom Python-fajl s dannymi GOST."""
    safe = _make_safe_name(gost_number)
    filepath = os.path.join(DATA_DIR, f'gost_{safe}.py')
    
    lines = [
        '# -*- coding: utf-8 -*-',
        f'"""Dannye GOST {gost_number}. {description}"""',
        '',
        'from modules.designation_generator import GostSpec',
        '',
        '',
        f'def get_gost_{safe}():',
        f'    """Returns spec for GOST {gost_number}."""',
        '    spec = GostSpec()',
        f'    spec.gost_number = {repr(gost_number)}',
        f'    spec.product_name = {repr(product_name)}',
        f'    spec.diameters = {repr(diameters)}',
        f'    spec.coarse_pitches = {repr(coarse)}',
        f'    spec.fine_pitches = {repr(fine)}',
        f'    spec.material_groups = {repr(groups)}',
        f'    spec.steel_grades = {repr(grades)}',
        f'    spec.coatings = {repr(coatings)}',
        f'    spec.format_coarse = {repr(format_coarse)}',
        f'    spec.format_fine = {repr(format_fine)}',
        '    return spec',
        '',
    ]
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    
    print(f"  Fajl sohranen: {filepath}")


def _register_gost(gost_number, product_name, description):
    """Dobavlyaem GOST v reestr (registry.json)."""
    registry = load_registry()
    safe = _make_safe_name(gost_number)
    
    # Klyuch dlya bystrogo dostupa (korotkij nomer)
    short_key = re.sub(r'[^0-9]', '', gost_number)[:5]
    if not short_key:
        short_key = safe[:10]
    
    registry[short_key] = {
        'module': f'data.gost_{safe}',
        'spec_func': f'get_gost_{safe}',
        'params_func': None,
        'name': f'GOST {gost_number} ({description or product_name})',
        'gost_number': gost_number,
    }
    
    save_registry(registry)
    print(f"  Zaregistrirovan s klyuchom: {short_key}")


def get_full_registry():
    """
    Vozvraschaet polnyj reestr: hardcoded + iz registry.json.
    Vyzyvaetsya iz GOST.py dlya polucheniya spiska vseh GOST.
    """
    # Hardcoded (vsegda est)
    from GOST import GOST_REGISTRY as hardcoded
    result = dict(hardcoded)
    
    # Iz JSON (dobavlennye cherez wizard)
    json_reg = load_registry()
    result.update(json_reg)
    
    return result
