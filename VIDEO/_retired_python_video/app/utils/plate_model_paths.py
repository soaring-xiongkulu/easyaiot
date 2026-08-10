"""VIDEO 根目录固定车牌模型路径"""
import os

_VIDEO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

PLATE_DETECT_MODEL_PATH = os.getenv(
    'PLATE_DETECT_MODEL_PATH',
    os.path.join(_VIDEO_ROOT, 'plate_detect.onnx'),
)
PLATE_REC_MODEL_PATH = os.getenv(
    'PLATE_REC_MODEL_PATH',
    os.path.join(_VIDEO_ROOT, 'plate_rec.onnx'),
)
