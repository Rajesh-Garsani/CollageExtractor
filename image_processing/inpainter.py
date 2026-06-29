import cv2
import numpy as np
import logging

logger = logging.getLogger("image_processing")


class ImageInpainter:
    @staticmethod
    def inpaint_exact_regions(image: np.ndarray, bounding_boxes: list) -> np.ndarray:
        if not bounding_boxes:
            return image

        logger.debug("Applying Perfect Comic Text Erasure.")
        result_image = image.copy()

        for (x, y, w, h) in bounding_boxes:
            # Pad slightly to cover the anti-aliased edges of the text font
            pad = 5
            x1, y1 = max(0, x - pad), max(0, y - pad)
            x2, y2 = min(image.shape[1], x + w + pad), min(image.shape[0], y + h + pad)

            roi = result_image[y1:y2, x1:x2]
            if roi.size == 0: continue

            # Create a precise mask of the dark text pixels
            gray_roi = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
            _, mask = cv2.threshold(gray_roi, 180, 255, cv2.THRESH_BINARY_INV)

            # Find the true background color by isolating the non-text pixels
            non_text_pixels = roi[mask == 0]
            if len(non_text_pixels) > 0:
                bg_color = np.median(non_text_pixels, axis=0).astype(int)
                std_dev = np.std(non_text_pixels, axis=0).mean()
            else:
                bg_color = np.array([255, 255, 255])
                std_dev = 0

            # Comic backgrounds are usually solid white/colors.
            # If uniform, paint a solid invisible box instead of blurring!
            if std_dev < 30:
                cv2.rectangle(result_image, (x1, y1), (x2, y2), bg_color.tolist(), -1)
            else:
                # Fallback for highly complex art backgrounds
                kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
                dilated_mask = cv2.dilate(mask, kernel, iterations=1)

                full_mask = np.zeros(image.shape[:2], dtype=np.uint8)
                full_mask[y1:y2, x1:x2] = dilated_mask

                result_image = cv2.inpaint(result_image, full_mask, 5, cv2.INPAINT_TELEA)

        return result_image