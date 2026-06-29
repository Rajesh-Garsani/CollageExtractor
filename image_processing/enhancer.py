import cv2
import numpy as np
import logging

logger = logging.getLogger("image_processing")


class ImageEnhancer:
    """Applies non-destructive visual enhancements to generated outputs."""

    @staticmethod
    def enhance_quality(image: np.ndarray) -> np.ndarray:
        logger.debug("Applying Pro-Level Enhancement Pipeline.")

        # 1. Bilateral Filter: Reduces compression noise while keeping edges razor-sharp
        denoised = cv2.bilateralFilter(image, d=9, sigmaColor=75, sigmaSpace=75)

        # 2. Unsharp Masking: Boosts micro-contrast for a high-res "AI" look
        gaussian = cv2.GaussianBlur(denoised, (0, 0), 2.0)
        sharpened = cv2.addWeighted(denoised, 1.5, gaussian, -0.5, 0)

        # 3. CLAHE (Contrast Limited Adaptive Histogram Equalization)
        # Applied only to the Lightness channel to make blacks deeper and whites crisper without destroying colors
        lab = cv2.cvtColor(sharpened, cv2.COLOR_BGR2LAB)
        l_channel, a_channel, b_channel = cv2.split(lab)

        clahe = cv2.createCLAHE(clipLimit=1.2, tileGridSize=(8, 8))
        cl = clahe.apply(l_channel)

        merged_lab = cv2.merge((cl, a_channel, b_channel))
        final_image = cv2.cvtColor(merged_lab, cv2.COLOR_LAB2BGR)

        return final_image