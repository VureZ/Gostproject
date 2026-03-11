"""
Modul dlya raboty s PDF.
Konvertiruet PDF v izobrazheniya cherez PyMuPDF (fitz) ili pdf2image.
"""

import os
import re
import logging
from typing import List, Dict, Optional
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Importy s proverkoj
try:
    import fitz  # PyMuPDF
    HAS_FITZ = True
except ImportError:
    HAS_FITZ = False

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

try:
    from pdf2image import convert_from_path
    HAS_PDF2IMAGE = True
except ImportError:
    HAS_PDF2IMAGE = False

try:
    from .config import POPPLER_PATH, PDF_DPI, OUTPUT_DIR, IMAGE_FORMAT
except ImportError:
    POPPLER_PATH = ''
    PDF_DPI = 300
    OUTPUT_DIR = 'output'
    IMAGE_FORMAT = 'PNG'


class PDFProcessor:
    """Obrabotka PDF fajlov i konvertaciya v izobrazheniya."""
    
    def __init__(self, pdf_path: str):
        self.pdf_path = Path(pdf_path)
        
        if not self.pdf_path.exists():
            raise FileNotFoundError(f"PDF ne najden: {pdf_path}")
        
        self.metadata = {'title': self.pdf_path.stem}
        self.total_pages = 0
        self.images = []

        # Metadata cherez PyMuPDF
        if HAS_FITZ:
            try:
                doc = fitz.open(str(self.pdf_path))
                self.total_pages = doc.page_count
                title = doc.metadata.get('title', '') if doc.metadata else ''
                self.metadata['title'] = title or self.pdf_path.stem
                doc.close()
            except Exception as e:
                logger.warning(f"Cannot read metadata: {e}")
        
        # GOST nomer iz imeni fajla
        match = re.search(r'(\d+[-_]\d+)', self.pdf_path.stem)
        if match:
            self.metadata['gost_number'] = match.group(1).replace('_', '-')
        
        logger.info(f"PDFProcessor: {self.pdf_path.name}, pages: {self.total_pages}")
    
    def convert_to_images(self, dpi=PDF_DPI,
                         first_page=None, last_page=None):
        """
        Konvertiruet PDF v spisok izobrazhenij PIL.Image.
        Probeet PyMuPDF, zatem pdf2image.
        """
        logger.info(f"Converting PDF (DPI={dpi})...")

        # Metod 1: PyMuPDF (bystree, ne trebuet Poppler)
        if HAS_FITZ and HAS_PIL:
            try:
                self.images = self._convert_pymupdf(dpi, first_page, last_page)
                logger.info(f"Converted (PyMuPDF): {len(self.images)} pages")
                return self.images
            except Exception as e:
                logger.warning(f"PyMuPDF failed: {e}")
        
        # Metod 2: pdf2image + Poppler
        if HAS_PDF2IMAGE:
            try:
                self.images = self._convert_pdf2image(dpi, first_page, last_page)
                logger.info(f"Converted (pdf2image): {len(self.images)} pages")
                return self.images
            except Exception as e:
                logger.error(f"pdf2image failed: {e}")
                raise
        
        raise RuntimeError("No PDF converter available (need PyMuPDF or pdf2image)")
    
    def _convert_pymupdf(self, dpi, first_page, last_page):
        """Konvertaciya cherez PyMuPDF (fitz)"""
        doc = fitz.open(str(self.pdf_path))
        images = []
        
        start = (first_page - 1) if first_page else 0
        end = last_page if last_page else doc.page_count
        zoom = dpi / 72.0
        matrix = fitz.Matrix(zoom, zoom)
        
        for page_num in range(start, end):
            page = doc[page_num]
            pix = page.get_pixmap(matrix=matrix)
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            images.append(img)
        
        doc.close()
        return images
    
    def _convert_pdf2image(self, dpi, first_page, last_page):
        """Konvertaciya cherez pdf2image + Poppler"""
        kwargs = {
            'pdf_path': str(self.pdf_path),
            'dpi': dpi,
            'fmt': IMAGE_FORMAT.lower(),
            'thread_count': 4,
        }
        if first_page:
            kwargs['first_page'] = first_page
        if last_page:
            kwargs['last_page'] = last_page
        if POPPLER_PATH and os.path.exists(POPPLER_PATH):
            kwargs['poppler_path'] = POPPLER_PATH
        
        return convert_from_path(**kwargs)
    
    def get_page_image(self, page_number):
        """Vozvraschaet izobrazhenie stranicy (numeraciya s 1)"""
        if not self.images:
            raise ValueError("Convert PDF first")
        if 1 <= page_number <= len(self.images):
            return self.images[page_number - 1]
        return None
    
    def get_info(self):
        return {
            'filename': self.pdf_path.name,
            'total_pages': self.total_pages,
            'metadata': self.metadata,
        }
