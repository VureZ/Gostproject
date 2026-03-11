# -*- coding: utf-8 -*-
"""
Dannye iz GOST ISO 4035-2014
Gajki shestigrannyje nizkie s faskoj (tip 0).
Klassy tochnosti A i B.

Oboznachenie: Gajka shestigrannaya nizkaya GOST ISO 4035 - M{d}-{class}
Primer: Gajka shestigrannaya nizkaya GOST ISO 4035 - M12-05
"""

from modules.designation_generator import GostSpec


def get_gost_iso_4035_2014() -> GostSpec:
    """Returns specification for GOST ISO 4035-2014."""
    
    spec = GostSpec()
    spec.gost_number = "ISO 4035-2014"
    spec.product_name = "Gajka shestigrannaya nizkaya"
    spec.tolerance = "6H"
    
    # ===== Tablica 1: Osnovnye rezby (str.8-9) =====
    spec.diameters = [
        "1.6", "2", "2.5", "3", "4", "5", "6", "8", "10", "12",
        "16", "20", "24", "30", "36", "42", "48", "56", "64",
    ]
    
    # ===== Krupnyj shag (ukazan v tablice kak P) =====
    spec.coarse_pitches = {
        "1.6": "0.35", "2": "0.4", "2.5": "0.45", "3": "0.5",
        "4": "0.7", "5": "0.8", "6": "1", "8": "1.25",
        "10": "1.5", "12": "1.75",
        "16": "2", "20": "2.5", "24": "3", "30": "3.5",
        "36": "4", "42": "4.5", "48": "5", "56": "5.5", "64": "6",
    }
    
    # ===== Melkij shag =====
    # GOST ISO 4035 ne opredelyaet melkij shag v tablice 1
    # No on vozmozen po ISO 724
    spec.fine_pitches = {}
    
    # ===== Klassy prochnosti (iz tablicy 3, str.10) =====
    # Dlya stali: 04, 05 (pri D ot M5 do M39)
    # Dlya nerzhavejki: A2-035, A4-035, A2-025, A4-025
    # Dlya cvetnogo metalla: po ISO 8839
    
    # Ispolzuem material_groups dlya klassov prochnosti
    # V etom GOSTe vmesto grupp materialov - klassy prochnosti
    spec.material_groups = {
        "04": "carbon",
        "05": "carbon",
        "A2-035": "stainless",
        "A4-035": "stainless",
        "A2-025": "stainless",
        "A4-025": "stainless",
    }
    
    # Marki stali dlya nerzhavejki
    spec.steel_grades = {
        "A2-035": ["A2"],
        "A4-035": ["A4"],
        "A2-025": ["A2"],
        "A4-025": ["A4"],
    }
    
    # Pokrytiya - v GOST ISO 4035 oni ne vhodyat v oboznachenie
    # (otdelka/pokrytie soglasovyvaetsya otdelno)
    spec.coatings = {}
    
    # Format oboznacheniya dlya GOST ISO 4035:
    # Gajka shestigrannaya nizkaya GOST ISO 4035 - M{d}-{class}
    spec.format_coarse = "{product} GOST {gost} - M{diameter}-{group}"
    spec.format_fine = "{product} GOST {gost} - M{diameter}x{pitch}-{group}"
    
    return spec
