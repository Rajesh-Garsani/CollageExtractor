import re
import logging
from typing import Dict, Any

logger = logging.getLogger("extractor")

class NLPParserService:
    """
    Parses natural language prompts to detect targeted panels and specific
    actions like text removal, upscaling, quality enhancement, and file format conversions.
    """

    def __init__(self) -> None:
        self.image_number_pattern = re.compile(
            r'\b(?:image|panel|img|number|no\.?)\s*(\d+)\b|\b(\d+)\b',
            re.IGNORECASE
        )
        self.upscale_pattern = re.compile(
            r'\b(?:upscale\s*(?:to\s*)?)?([248])x\b',
            re.IGNORECASE
        )

    def parse_prompt(self, raw_prompt: str) -> Dict[str, Any]:
        logger.info(f"Parsing raw prompt string: '{raw_prompt}'")
        normalized = raw_prompt.lower().strip()

        intent: Dict[str, Any] = {
            "target_image_number": None,
            "actions": {
                "remove_all_text": False,
                "remove_title": False,
                "remove_panel_number": False,
                "keep_caption": True,
                "enhance_quality": False,
                "upscale_factor": 1,
                "target_width": None,
                "target_height": None,
                "output_format": "png"
            },
            "raw_exclusion_text": None
        }

        # 1. Target Image Number
        match_number = self.image_number_pattern.search(normalized)
        if match_number:
            intent["target_image_number"] = match_number.group(1) or match_number.group(2)

        # 2. Exact Dimensions (UPGRADED: More flexible matching)
        dim_match = re.search(r'(?:size\s*)?(\d+)\s*(?:x|×|by)\s*(\d+)', normalized)
        if dim_match:
            intent["actions"]["target_width"] = int(dim_match.group(1))
            intent["actions"]["target_height"] = int(dim_match.group(2))

        # 3. Specific Text Removal
        quoted_text_match = re.search(r'remove\s*["\']([^"\']+)["\']', raw_prompt, re.IGNORECASE)
        if quoted_text_match:
            intent["raw_exclusion_text"] = quoted_text_match.group(1)
        elif "remove all text" in normalized or "remove text" in normalized:
            intent["actions"]["remove_all_text"] = True

        # 4. Upscaling & Formats
        match_upscale = self.upscale_pattern.search(normalized)
        if match_upscale:
            intent["actions"]["upscale_factor"] = int(match_upscale.group(1))

        if "enhance" in normalized: intent["actions"]["enhance_quality"] = True

        for fmt in ["png", "jpg", "jpeg", "webp"]:
            if f"in {fmt}" in normalized or f"to {fmt}" in normalized or normalized.endswith(fmt):
                intent["actions"]["output_format"] = "jpeg" if fmt == "jpg" else fmt
                break

        return intent