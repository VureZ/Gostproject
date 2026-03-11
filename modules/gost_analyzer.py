"""
Modul analiza dokumentov GOST/OST.
Nahodit v tekste: nomer GOST, nazvanie, primer oboznacheniya, parametry.

Uchityvaet nizkoye kachestvo OCR (oshibki v bukwah).
"""

import re
import logging
from typing import List, Dict, Optional
from dataclasses import dataclass, field

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class DesignationTemplate:
    gost_number: str = ""
    product_name: str = ""
    raw_example: str = ""
    template_parts: List[Dict] = field(default_factory=list)


@dataclass 
class GostData:
    gost_number: str = ""
    product_name: str = ""
    designation_template: Optional[DesignationTemplate] = None
    diameters: List[str] = field(default_factory=list)
    pitches_coarse: List[str] = field(default_factory=list)
    pitches_fine: List[str] = field(default_factory=list)
    material_groups: List[str] = field(default_factory=list)
    strength_classes: List[str] = field(default_factory=list)
    coatings: List[str] = field(default_factory=list)
    raw_tables: List = field(default_factory=list)
    full_text: str = ""


class GostAnalyzer:
    """Analizator GOST. Uchityvaet oshibki OCR."""
    
    def __init__(self):
        self.data = GostData()
    
    def analyze_text(self, pages_text: List[str]) -> GostData:
        full_text = '\n\n'.join(pages_text)
        self.data.full_text = full_text
        
        self.data.gost_number = self._find_gost_number(full_text)
        logger.info("GOST: %s", self.data.gost_number)
        
        self.data.product_name = self._find_product_name(full_text)
        logger.info("Product: %s", self.data.product_name)
        
        self.data.designation_template = self._find_designation(full_text)
        if self.data.designation_template:
            logger.info("Designation: %s", self.data.designation_template.raw_example)
        
        return self.data
    
    def _find_gost_number(self, text: str) -> str:
        """Finds GOST number. OCR may produce: gst, gOCT, TOCT etc."""
        # Flexible pattern for OCR errors
        patterns = [
            r'[гГгTr][оOоCc][сSс][тTт]\s+[Ii][Ss][Oo]\s+([\d]+[-—.]+\d+)',
            r'[гГгTr][оOоCc][сSсe][тTт]\s+([\d]+[-—.]+\d+)',
            r'[гГ][сCc][тTт]\s+([\d]+[-—.]+\d+)',
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                number = match.group(1)
                number = re.sub(r'[-—.]+', '-', number)
                return number
        return "unknown"
    
    def _find_product_name(self, text: str) -> str:
        """Finds product name. OCR may give: aйkи, ECTH, AЙКИ etc."""
        text_lower = text.lower()
        
        # Check for keywords with OCR tolerance
        if any(kw in text_lower for kw in ['гайк', 'айк', 'айки', 'aйk']):
            return "Gajka"
        if any(kw in text_lower for kw in ['болт', 'олт', 'oлт']):
            return "Bolt"
        if any(kw in text_lower for kw in ['винт', 'инт']):
            return "Vint"
        if any(kw in text_lower for kw in ['шпильк', 'пильк']):
            return "Shpilka"
        if any(kw in text_lower for kw in ['шайб', 'айб']):
            return "Shajba"
        return "Izdelie"
    
    def _find_designation(self, text: str) -> Optional[DesignationTemplate]:
        """
        Finds designation example.
        OCR text example:
          'айка м 36.05.019 гOCт 10605--914'
          'айка S0x 4 21. ЭХХШЭТ IOCТ 10605.'
        """
        template = DesignationTemplate()
        template.gost_number = self.data.gost_number
        template.product_name = self.data.product_name
        
        # Flexible search for designation pattern
        # Look for: [aА]йк[аa] [мМMm] <number>...<GOST>
        # OCR may distort letters but numbers are usually OK
        patterns = [
            # Gajka M <d>.<group>.<coating> GOST <number>
            r'[аaА]йк[аa]\s+[мМMm]\s*(\d+[\.,]\d+[\.,]\d+)\s+[гГгTr][оOоCc][сSс][тTт]\s*([\d\-—.]+)',
            r'[аaА]йк[аa]\s+[мМMm]\s*(\d+)\s*[xх×Xx]\s*(\d+)\s+(\d+[\.,]?\s*\S+)\s+[гГTr][оOоCc][сSс][тTт]',
            # Generic: M <number> ... GOST
            r'[мМMm]\s*(\d{2,3}[\.,]\d+[\.,]\d+)\s+[гГTr]',
            # With x: M <d> x <pitch> <group>
            r'[мМMm]\s*(\d{2,3})\s*[xхXх×]\s*(\d+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                template.raw_example = match.group(0).strip()
                logger.info("Found designation: %s", template.raw_example)
                
                # Parse context around the match
                start = max(0, match.start() - 300)
                end = min(len(text), match.end() + 100)
                context = text[start:end]
                template.template_parts = self._parse_context(context, match)
                return template
        
        # Fallback: search for any "M <number>" pattern near "GOST"
        match = re.search(r'[мМMm]\s+(\d{2,3})', text)
        if match:
            template.raw_example = match.group(0).strip()
            return template
        
        logger.warning("Designation not found in OCR text")
        return None
    
    def _parse_context(self, context: str, match) -> List[Dict]:
        """Parse the context around designation to extract parameter info."""
        info = {}
        
        # Diameter (number after M)
        m = re.search(r'[мМMm]\s*(\d{2,3})', context)
        if m:
            info['diameter'] = m.group(1)
        
        # Thread pitch (after x)
        m = re.search(r'[xхXх×]\s*(\d+[.,]?\d*)', context)
        if m:
            info['pitch'] = m.group(1).replace(',', '.')
        
        # Material group (2-digit number: 02-25)
        groups_found = re.findall(r'\b(0[2-9]|[12]\d)\b', context)
        if groups_found:
            info['material_groups'] = groups_found
        
        # Coating (3-digit: 019, etc)
        m = re.search(r'\b(0\d{2})\b', context)
        if m:
            info['coating'] = m.group(1)
        
        return [{'type': 'context', 'value': info}]
    
    def extract_parameters_from_tables(self, tables) -> Dict:
        """Extract parameters from found tables."""
        params = {
            'diameters': [],
            'pitches_coarse': [],
            'pitches_fine': [],
            'material_groups': [],
            'strength_classes': [],
        }
        
        for table in tables:
            self._analyze_table(table, params)
        
        # Also extract from full text
        self._extract_from_text(params)
        
        # Deduplicate
        for key in params:
            params[key] = list(dict.fromkeys(params[key]))
        
        return params
    
    def _analyze_table(self, table, params):
        """Analyze table content for parameters."""
        if not table.headers:
            return
        
        all_text = ' '.join(table.headers)
        for row in table.rows:
            all_text += ' ' + ' '.join(row)
        all_lower = all_text.lower()
        
        # Look for diameters in table rows
        for row in [table.headers] + table.rows:
            row_text = ' '.join(row).lower()
            if any(kw in row_text for kw in ['резьб', 'езьб', 'резь', 'd']):
                for cell in row:
                    cell_clean = cell.strip('() ')
                    if re.match(r'^\d{2,3}$', cell_clean):
                        d = int(cell_clean)
                        if 1 <= d <= 200:  # reasonable diameter range
                            params['diameters'].append(cell_clean)
        
        # Material groups (02, 04, 05, 06, 07, 11, 21, 23, 25)
        if any(kw in all_lower for kw in ['групп', 'рупп', 'материал', 'атериал']):
            groups = re.findall(r'\b(0[2-7]|1[1]|2[1-5])\b', all_text)
            params['material_groups'].extend(groups)
    
    def _extract_from_text(self, params):
        """Extract parameters from full OCR text."""
        text = self.data.full_text
        
        # Material groups from text: "02, 04, 05, 06, 07" or "11, 21, 23, 25"
        # Look for sequences of 2-digit numbers
        group_pattern = r'(0[2-7])\s*[,.\s]+\s*(0[2-7])'
        for m in re.finditer(group_pattern, text):
            params['material_groups'].extend([m.group(1), m.group(2)])
        
        group_pattern2 = r'([12][1-5])\s*[,.\s]+\s*([12][1-5])'
        for m in re.finditer(group_pattern2, text):
            params['material_groups'].extend([m.group(1), m.group(2)])
    
    def get_summary(self) -> str:
        lines = [
            "GOST: " + self.data.gost_number,
            "Product: " + self.data.product_name,
        ]
        
        if self.data.designation_template:
            lines.append("Designation: " + self.data.designation_template.raw_example)
            if self.data.designation_template.template_parts:
                ctx = self.data.designation_template.template_parts
                for p in ctx:
                    if p.get('type') == 'context':
                        lines.append("Context: " + str(p.get('value', {})))
        
        if self.data.diameters:
            lines.append("Diameters: " + ', '.join(self.data.diameters))
        if self.data.material_groups:
            lines.append("Material groups: " + ', '.join(self.data.material_groups))
        if self.data.pitches_coarse:
            lines.append("Coarse pitches: " + ', '.join(self.data.pitches_coarse))
        if self.data.pitches_fine:
            lines.append("Fine pitches: " + ', '.join(self.data.pitches_fine))
        
        return '\n'.join(lines)
