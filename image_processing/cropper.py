import cv2
import numpy as np
import logging

logger = logging.getLogger("image_processing")


class ImageCropper:
    """Handles precision extraction of image panels and border removal."""

    @staticmethod
    def crop_panel(image: np.ndarray, x: int, y: int, w: int, h: int) -> np.ndarray:
        """Extracts a specific rectangular region from the image array."""
        logger.debug(f"Cropping image region: x={x}, y={y}, w={w}, h={h}")
        max_h, max_w = image.shape[:2]
        x1, y1 = max(0, x), max(0, y)
        x2, y2 = min(max_w, x + w), min(max_h, y + h)

        return image[y1:y2, x1:x2]

    @staticmethod
    def auto_remove_borders(image: np.ndarray) -> np.ndarray:
        """
        DISABLED AGGRESSIVE CROPPING.
        Only shaves a safe 2-pixel margin to remove any bleed from adjacent grid lines.
        Does NOT contour-crop the artwork inside the panel.
        """
        logger.debug("Applying safe margin trim (disabled aggressive internal cropping).")
        buffer = 2
        h, w = image.shape[:2]

        if h > buffer * 2 and w > buffer * 2:
            y_start = buffer
            y_end = h - buffer
            x_start = buffer
            x_end = w - buffer
            return image[y_start:y_end, x_start:x_end]

        return image