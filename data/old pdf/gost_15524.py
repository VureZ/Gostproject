# -*- coding: utf-8 -*-
"""
Dannye iz GOST 15524
Gajki shestigrannyje s diametrom rezby svyshe 48 mm, klassa tochnosti B.
Dannye izvlecheny vruchuju iz PDF (stranicy 4-6).
"""

from modules.designation_generator import GostSpec


def get_gost_15524() -> GostSpec:
    """Returns complete specification for GOST 10605-94."""
    
    spec = GostSpec()
    spec.gost_number = "15524"
    spec.product_name = "Bolt"
    spec.tolerance = "48mm"
    
    # ===== Tablica 1: Diametry rezby (str. 4) =====
    spec.diameters = [
        "52", "56", "64", "72", "76",
        "80", "90", "100", "110", "125", "140", "150"
    ]
    
    # ===== Krupnyj shag (P) =====
    spec.coarse_pitches = {
        "52": "5.0", "56": "5.5", "64": "6.0",
    }
    
    # ===== Melkij shag =====
    spec.fine_pitches = {
        "52": ["3.0"], "56": ["3.0"], "64": ["4.0"],
        "72": ["4.0", "6.0"], "76": ["4.0", "6.0"],
        "80": ["4.0", "6.0"], "90": ["4.0", "6.0"],
        "100": ["4.0", "6.0"], "110": ["4.0", "6.0"],
        "125": ["4.0", "6.0"], "140": ["4.0", "6.0"],
        "150": ["4.0", "6.0"],
    }
    
    # ===== Gruppy materialov (tabl. 2, str. 5) =====
    spec.material_groups = {
        "02": "carbon", "04": "carbon", "05": "carbon",
        "06": "carbon", "07": "carbon",
        "11": "stainless", "21": "stainless",
        "23": "stainless", "25": "stainless",
    }
    
    spec.steel_grades = {
        "11": ["12X18H10T"],
        "21": ["12X18H9T", "12X18H10T"],
        "23": ["08X18H10T"],
        "25": ["10X17H13M2T"],
    }
    
    spec.coatings = {
        "019": "Zn chr 9mkm",
        "029": "Zn chr 9mkm barrel",
        "016": "Zn 6mkm",
    }
    
    return spec


def get_parameters_10605_94():
    """
    Returns ProductParameters rows from Tablica 1 (str. 4 PDF).
    Razmery gaek po diametram.
    """
    # Kolonki tablicy 1:
    #   d, P_krupnyj, P_melkij, da_min, da_max, dw_min,
    #   e_min, m_max, m_min, m'_min, S_nom_max, S_min
    
    # Dannye iz tablicy 1 GOST 10605-94 (str. 4)
    table_data = [
        # d    P_kr  P_mel  da_min da_max dw_min  e_min    m_max m_min m'_min S_nom S_min
        ("52", "5.0","3.0", 52.0, 56.2,  74.2,   88.25,   42,   40.4, 32.3,  80,   78.1),
        ("56", "5.5","3.0", 56.0, 60.5,  78.7,   93.56,   45,   43.4, 34.7,  85,   82.8),
        ("64", "6.0","4.0", 64.0, 69.1,  88.2,  104.86,   51,   49.1, 39.3,  95,   92.8),
        ("72", "",   "4.0", 72.0, 77.8,  97.7,  116.16,   58,   56.1, 44.9, 105,  102.8),
        ("76", "",   "4.0", 76.0, 82.1, 102.4,  121.81,   61,   59.1, 47.3, 110,  107.8),
        ("80", "",   "4.0", 80.0, 86.4, 107.2,  127.46,   64,   62.1, 49.7, 115,  112.8),
        ("90", "",   "4.0", 90.0, 97.2, 121.1,  144.08,   72,   70.1, 56.1, 130,  127.5),
        ("100","",   "4.0",100.0,108.0, 135.4,  161.03,   80,   78.1, 62.5, 145,  142.5),
        ("110","",   "4.0",110.0,118.8, 144.9,  172.33,   88,   85.8, 68.6, 155,  152.5),
        ("125","",   "4.0",125.0,135.0, 168.6,  200.58,  100,   97.8, 78.2, 180,  177.5),
        ("140","",   "4.0",140.0,151.2, 187.2,  222.72,  112,  109.8, 87.8, 200,  197.1),
        ("150","",   "4.0",150.0,162.0, 211.0,  250.97,  128,  125.5,100.4, 225,  222.1),
    ]
    
    rows = []
    gost = "10605-94"
    
    for d, p_kr, p_mel, da_min, da_max, dw_min, e_min, m_max, m_min, mp_min, s_nom, s_min in table_data:
        # Row for coarse pitch (if exists)
        if p_kr:
            rows.append({
                'GOST_Number': gost,
                'ThreadDiameter': float(d),
                'ThreadPitch': p_kr,
                'PitchType': 'coarse',
                'MaterialGroup': '',
                'Parameter_da_min': da_min,
                'Parameter_da_max': da_max,
                'Parameter_dw_min': dw_min,
                'Parameter_e_min': e_min,
                'Parameter_m_max': float(m_max),
                'Parameter_m_min': float(m_min),
                'Parameter_m_prime_min': float(mp_min),
                'Parameter_S_nom_max': float(s_nom),
                'Parameter_S_min': float(s_min),
                'TheoreticalMass': None,
            })
        
        # Row for fine pitch
        if p_mel:
            rows.append({
                'GOST_Number': gost,
                'ThreadDiameter': float(d),
                'ThreadPitch': p_mel,
                'PitchType': 'fine',
                'MaterialGroup': '',
                'Parameter_da_min': da_min,
                'Parameter_da_max': da_max,
                'Parameter_dw_min': dw_min,
                'Parameter_e_min': e_min,
                'Parameter_m_max': float(m_max),
                'Parameter_m_min': float(m_min),
                'Parameter_m_prime_min': float(mp_min),
                'Parameter_S_nom_max': float(s_nom),
                'Parameter_S_min': float(s_min),
                'TheoreticalMass': None,
            })
    
    return rows
