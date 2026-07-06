from __future__ import annotations

import cv2
import numpy as np
from PIL import Image

from schemas import EnhancementParams


def _to_uint8(image: np.ndarray) -> np.ndarray:
    return np.clip(image, 0, 255).astype(np.uint8)


def _apply_gamma(image: np.ndarray, gamma: float) -> np.ndarray:
    if abs(gamma - 1.0) < 0.01:
        return image
    inverse = 1.0 / gamma
    table = np.array([((i / 255.0) ** inverse) * 255 for i in range(256)], dtype=np.uint8)
    return cv2.LUT(image, table)


def _as_gray(image: np.ndarray) -> np.ndarray:
    if image.ndim == 2:
        return image
    return cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)


def _sharpen(image: np.ndarray, amount: float) -> np.ndarray:
    if amount <= 0:
        return image
    blur = cv2.GaussianBlur(image, (0, 0), sigmaX=1.0)
    return cv2.addWeighted(image, 1.0 + amount, blur, -amount, 0)


def _denoise(image: np.ndarray, amount: float) -> np.ndarray:
    if amount <= 0:
        return image
    strength = max(3, int(3 + amount * 4))
    if image.ndim == 2:
        return cv2.fastNlMeansDenoising(image, None, strength, 7, 21)
    return cv2.fastNlMeansDenoisingColored(image, None, strength, strength, 7, 21)


def _boost_edges(gray: np.ndarray, amount: float) -> np.ndarray:
    if amount <= 0:
        return gray
    edges = cv2.Canny(gray, 80, 180)
    darken = np.zeros_like(gray)
    darken[edges > 0] = int(18 * amount)
    return _to_uint8(gray.astype(np.int16) - darken.astype(np.int16))


def _boost_edges_color(image: np.ndarray, amount: float) -> np.ndarray:
    if amount <= 0:
        return image
    gray = _as_gray(image)
    edges = cv2.Canny(gray, 80, 180)
    darken = np.zeros_like(gray, dtype=np.int16)
    darken[edges > 0] = int(18 * amount)
    return _to_uint8(image.astype(np.int16) - darken[:, :, None])


def _apply_threshold(gray: np.ndarray, params: EnhancementParams) -> np.ndarray:
    if params.adaptive_threshold:
        # Adaptive thresholding keeps text and fine plan lines visible when the scan is unevenly lit.
        return cv2.adaptiveThreshold(
            gray,
            255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            35,
            11,
        )
    if params.threshold_enabled:
        _, binary = cv2.threshold(gray, params.threshold_value, 255, cv2.THRESH_BINARY)
        return binary
    return gray


def _strengthen_lines(gray: np.ndarray, line_thicken: int, morph_close: int) -> np.ndarray:
    if line_thicken <= 0 and morph_close <= 0:
        return gray

    # Work on an inverted foreground mask: plan strokes become white, so dilation and closing
    # make faint or interrupted lines more continuous before converting back to normal polarity.
    foreground = 255 - gray

    if line_thicken > 0:
        kernel_size = 1 + line_thicken
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (kernel_size, kernel_size))
        foreground = cv2.dilate(foreground, kernel, iterations=1)

    if morph_close > 0:
        kernel_size = 1 + morph_close * 2
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (kernel_size, kernel_size))
        foreground = cv2.morphologyEx(foreground, cv2.MORPH_CLOSE, kernel, iterations=1)

    return 255 - foreground


def enhance_image(image: Image.Image, params: EnhancementParams) -> Image.Image:
    """Enhance a rendered PDF page for technical plan readability."""
    rgb = image.convert("RGB")
    arr = np.array(rgb)

    # Brightness and contrast are applied early so later steps receive clearer stroke data.
    arr = arr.astype(np.float32)
    arr = (arr - 127.5) * params.contrast + 127.5
    arr = arr * params.brightness
    arr = _to_uint8(arr)

    arr = _apply_gamma(arr, params.gamma)
    arr = _denoise(arr, params.denoise)
    arr = _sharpen(arr, params.sharpen)

    needs_binary_or_gray_pipeline = (
        params.grayscale
        or params.threshold_enabled
        or params.adaptive_threshold
        or params.line_thicken > 0
        or params.morph_close > 0
    )

    if needs_binary_or_gray_pipeline:
        gray = _as_gray(arr)
        gray = _boost_edges(gray, params.edge_boost)
        gray = _apply_threshold(gray, params)
        gray = _strengthen_lines(gray, params.line_thicken, params.morph_close)
        result = gray
    else:
        result = _boost_edges_color(arr, params.edge_boost)

    if params.invert:
        result = 255 - result

    if result.ndim == 2:
        return Image.fromarray(result, mode="L").convert("RGB")
    return Image.fromarray(result, mode="RGB")
