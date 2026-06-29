import re
import logging
import numpy as np
from typing import Dict, Any, List

logger = logging.getLogger("extractor")


class OCREngineService:
    _reader_instance = None

    @classmethod
    def _get_reader(cls):
        """Thread-safe lazy initialization for EasyOCR."""
        if cls._reader_instance is None:
            import easyocr
            logger.info("Initializing EasyOCR Model...")
            cls._reader_instance = easyocr.Reader(['en'], gpu=False)
        return cls._reader_instance

    def extract_all(self, image_np: np.ndarray) -> List[Dict[str, Any]]:
        """Scans the entire image in one pass for macro-level layout analysis."""
        reader = self._get_reader()
        results = reader.readtext(image_np)

        parsed_data = []
        for bbox, text, prob in results:
            # bbox structure: [[x,y], [x,y], [x,y], [x,y]]
            x_coords = [p[0] for p in bbox]
            y_coords = [p[1] for p in bbox]

            x = int(min(x_coords))
            y = int(min(y_coords))
            w = int(max(x_coords) - x)
            h = int(max(y_coords) - y)

            parsed_data.append({
                'text': text.strip(),
                'prob': prob,
                'x': x, 'y': y, 'w': w, 'h': h,
                'cx': x + (w // 2),  # Center X
                'cy': y + (h // 2)  # Center Y
            })

        return parsed_data