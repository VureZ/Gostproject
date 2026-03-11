"""
Модуль OCR распознавания. Использует PaddleOCR 2.7.3.
"""

import os
os.environ['FLAGS_use_mkldnn'] = '0'
os.environ['FLAGS_use_onednn'] = '0'
os.environ['PADDLE_USE_ONEDNN'] = '0'

import cv2
import numpy as np
from PIL import Image
from typing import List, Dict, Optional, Any
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

PADDLEOCR_AVAILABLE = False
PPSTRUCTURE_AVAILABLE = False
PADDLEOCR_VERSION = None

try:
    import paddle
    from paddleocr import PaddleOCR
    import paddleocr
    PADDLEOCR_VERSION = paddleocr.__version__
    PADDLEOCR_AVAILABLE = True
    logger.info(f"PaddleOCR {PADDLEOCR_VERSION} - OK")
    try:
        from paddleocr import PPStructure
        PPSTRUCTURE_AVAILABLE = True
    except ImportError:
        pass
except ImportError as e:
    logger.error(f"PaddleOCR not installed: {e}")

try:
    from .config import (
        OCR_LANGUAGE, USE_ANGLE_CLASSIFICATION,
        USE_GPU, OCR_CONFIDENCE_THRESHOLD
    )
except ImportError:
    OCR_LANGUAGE = 'ru'
    USE_ANGLE_CLASSIFICATION = True
    USE_GPU = False
    OCR_CONFIDENCE_THRESHOLD = 0.6


class OCREngine:
    """Движок OCR на базе PaddleOCR."""
    
    def __init__(self, language=OCR_LANGUAGE,
                 use_gpu=USE_GPU,
                 use_angle_cls=USE_ANGLE_CLASSIFICATION):
        if not PADDLEOCR_AVAILABLE:
            raise ImportError("PaddleOCR ne ustanovlen!")
        
        self.language = language
        self.use_gpu = use_gpu
        self.use_angle_cls = use_angle_cls
        self.version = PADDLEOCR_VERSION
        
        logger.info(f"Initializing OCR (lang={language}, gpu={use_gpu})...")
        
        self.ocr = PaddleOCR(
            use_angle_cls=use_angle_cls,
            lang=language,
            use_gpu=use_gpu,
            show_log=False,
            enable_mkldnn=False
        )
        logger.info("OCR engine ready")
    
    def recognize_text(self, image, 
                      confidence_threshold=OCR_CONFIDENCE_THRESHOLD):
        """
        Recognizes text in image.
        Returns list of {text, confidence, bbox}.
        """
        img_array = self._prepare_image(image)
        
        try:
            result = self.ocr.ocr(img_array, cls=self.use_angle_cls)
            
            if not result or not result[0]:
                return []
            
            recognized = []
            for line in result[0]:
                bbox = line[0]
                text, confidence = line[1]
                if confidence >= confidence_threshold:
                    recognized.append({
                        'text': text,
                        'confidence': confidence,
                        'bbox': bbox
                    })
            
            logger.info(f"Recognized: {len(recognized)} items")
            return recognized
            
        except Exception as e:
            logger.error(f"OCR error: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return []
    
    def _prepare_image(self, image):
        """Converts image to numpy array (BGR)."""
        if isinstance(image, str):
            if not os.path.exists(image):
                raise FileNotFoundError(f"Image not found: {image}")
            return cv2.imread(image)
        elif isinstance(image, Image.Image):
            img = np.array(image)
            if len(img.shape) == 3 and img.shape[2] == 3:
                img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
            return img
        elif isinstance(image, np.ndarray):
            return image
        else:
            raise ValueError(f"Unsupported image type: {type(image)}")
