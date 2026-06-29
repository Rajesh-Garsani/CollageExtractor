import cv2
import numpy as np
import logging
import re

logger = logging.getLogger("extractor")


class VisionService:
    @staticmethod
    def load_image_rgb(image_path: str) -> np.ndarray:
        img = cv2.imread(image_path)
        if img is None: raise FileNotFoundError()
        return cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

    def infer_panels(self, image_np: np.ndarray, ocr_data: list) -> list:
        img_h, img_w = image_np.shape[:2]
        gray = cv2.cvtColor(image_np, cv2.COLOR_RGB2GRAY)

        # 1. Threshold to isolate the black lines
        thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 11, 2)

        # 2. Morphological close to connect slightly broken drawn lines
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        closed = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel, iterations=1)

        # 3. Find all contours
        contours, _ = cv2.findContours(closed, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)

        used_rects = []
        total_area = img_w * img_h
        min_area = total_area * 0.005  # At least 0.5% of the image
        max_area = total_area * 0.95  # Ignore the entire page

        # Mathematically calculates if two boxes are nearly identical
        def calculate_iou(b1, b2):
            x1, y1, w1, h1 = b1
            x2, y2, w2, h2 = b2
            ix = max(x1, x2);
            iy = max(y1, y2)
            iw = max(0, min(x1 + w1, x2 + w2) - ix)
            ih = max(0, min(y1 + h1, y2 + h2) - iy)
            if iw > 0 and ih > 0:
                inter_area = iw * ih
                union_area = (w1 * h1) + (w2 * h2) - inter_area
                return inter_area / float(union_area) if union_area > 0 else 0
            return 0

        # Filter contours by size, shape, and deduplicate
        for cnt in contours:
            x, y, w, h = cv2.boundingRect(cnt)
            area = w * h

            if min_area < area < max_area:
                # Aspect ratio filter (ignore super skinny strips)
                if 0.2 < (w / float(h)) < 5.0:
                    # Rectangularity filter: ensures we ignore round character heads
                    cnt_area = cv2.contourArea(cnt)
                    extent = cnt_area / float(area) if area > 0 else 0
                    if extent > 0.75:  # Must be fairly rectangular
                        rect = (x, y, w, h)

                        # De-duplicate identical boxes (IoU > 60% overlap)
                        is_dup = False
                        for e_rect in used_rects:
                            if calculate_iou(rect, e_rect) > 0.6:
                                is_dup = True
                                break

                        if not is_dup:
                            used_rects.append(rect)

        # 4. Container filtering: Discard large boxes that enclose other panels
        # (This prevents the outer page margin from eating the smaller panels)
        final_rects = []
        for i, b1 in enumerate(used_rects):
            x1, y1, w1, h1 = b1
            is_container = False
            for j, b2 in enumerate(used_rects):
                if i == j: continue
                x2, y2, w2, h2 = b2
                # Check if box2 is heavily inside box1
                ix = max(x1, x2);
                iy = max(y1, y2)
                iw = max(0, min(x1 + w1, x2 + w2) - ix)
                ih = max(0, min(y1 + h1, y2 + h2) - iy)
                if iw > 0 and ih > 0:
                    inter_area = iw * ih
                    if inter_area / float(w2 * h2) > 0.8:  # Box2 is 80% inside Box1
                        is_container = True
                        break

            if not is_container:
                final_rects.append(b1)

        panels = []
        # Sort top-to-bottom, left-to-right to maintain reading order
        avg_h = sum(b[3] for b in final_rects) / len(final_rects) if final_rects else img_h
        final_rects.sort(key=lambda b: (b[1] // (avg_h * 0.5), b[0]))

        for idx, (x, y, w, h) in enumerate(final_rects):
            # Pad slightly to avoid the black grid line itself
            pad = 2
            px, py = x + pad, y + pad
            pw, ph = w - (pad * 2), h - (pad * 2)

            panel_ocr = [item for item in ocr_data if px <= item['cx'] <= px + pw and py <= item['cy'] <= py + ph]
            full_text = "\n".join([i['text'] for i in panel_ocr])

            # Extract panel number (e.g., "No. 175" or just "175")
            image_num = ""
            match = re.search(r'No\.?\s*(\d+)', full_text, re.IGNORECASE)
            if match:
                image_num = match.group(1)
            else:
                digits = re.findall(r'\d+', full_text)
                image_num = digits[0] if digits else str(idx)

            panels.append({
                "panel_index": idx,
                "x_coord": px, "y_coord": py,
                "width": pw, "height": ph,
                "header_height": int(ph * 0.20),
                "has_borders": True,
                "ocr_image_number": image_num,
                "ocr_raw_text": full_text,
                "ocr_confidence": 1.0
            })

        # Fallback if entirely empty
        if not panels:
            panels.append({
                "panel_index": 0, "x_coord": 0, "y_coord": 0,
                "width": img_w, "height": img_h,
                "header_height": 0, "has_borders": False,
                "ocr_image_number": "1", "ocr_raw_text": "", "ocr_confidence": 1.0
            })

        return panels