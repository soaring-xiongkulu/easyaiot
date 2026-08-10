import cv2
import numpy as np


def get_split_merge(img: np.ndarray) -> np.ndarray:
    h, w, _ = img.shape
    img_upper = img[0 : int(5 / 12 * h), :]
    img_lower = img[int(1 / 3 * h) :, :]
    img_upper = cv2.resize(img_upper, (img_lower.shape[1], img_lower.shape[0]))
    return np.hstack((img_upper, img_lower))
