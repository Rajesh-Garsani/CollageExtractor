import cv2
import numpy as np
import logging
from abc import ABC, abstractmethod
import torch
from basicsr.archs.rrdbnet_arch import RRDBNet
from realesrgan import RealESRGANer

logger = logging.getLogger("image_processing")


class BaseUpscaler(ABC):
    @abstractmethod
    def upscale(self, image: np.ndarray, scale_factor: int) -> np.ndarray:
        pass


class RealESRGANUpscaler(BaseUpscaler):
    """Pro-Level AI Upscaler using Real-ESRGAN (CPU Optimized)"""

    def __init__(self):
        logger.info("Initializing Real-ESRGAN Anime Model...")

        # Define architecture for the anime model (best for comic strips)
        model = RRDBNet(num_in_ch=3, num_out_ch=3, num_feat=64, num_block=6, num_grow_ch=32, scale=4)
        model_path = 'https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.2.4/RealESRGAN_x4plus_anime_6B.pth'

        # Force CPU device
        device = torch.device('cpu')

        # Initialize the wrapper
        self.upsampler = RealESRGANer(
            scale=4,
            model_path=model_path,
            dni_weight=None,
            model=model,
            tile=400,  # CRITICAL FOR CPU: Chunks the image to prevent RAM crashes
            tile_pad=10,
            pre_pad=0,
            half=False,  # Must be False for CPU
            device=device
        )

    def upscale(self, image: np.ndarray, scale_factor: int) -> np.ndarray:
        if scale_factor <= 1:
            return image

        logger.info(f"Executing Deep Upscale {scale_factor}x using Real-ESRGAN...")
        try:
            # Real-ESRGAN output
            output, _ = self.upsampler.enhance(image, outscale=scale_factor)
            return output
        except Exception as e:
            logger.error(f"Real-ESRGAN failed: {str(e)}. Falling back to Lanczos.")
            new_width = int(image.shape[1] * scale_factor)
            new_height = int(image.shape[0] * scale_factor)
            return cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_LANCZOS4)


class ImageUpscaler:
    def __init__(self):
        self._strategy: BaseUpscaler = RealESRGANUpscaler()

    def process(self, image: np.ndarray, scale_factor: int) -> np.ndarray:
        return self._strategy.upscale(image, scale_factor)

    def resize_to_target(self, image: np.ndarray, target_w: int, target_h: int) -> np.ndarray:
        scale = min(target_w / image.shape[1], target_h / image.shape[0])
        new_w, new_h = int(image.shape[1] * scale), int(image.shape[0] * scale)
        resized = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_LANCZOS4)
        canvas = np.full((target_h, target_w, 3), 255, dtype=np.uint8)
        x_off, y_off = (target_w - new_w) // 2, (target_h - new_h) // 2
        canvas[y_off:y_off + new_h, x_off:x_off + new_w] = resized
        return canvas