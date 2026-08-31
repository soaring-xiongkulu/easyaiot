"""VIDEO 根目录固定人脸模型路径（单文件，短命名）"""
import os

_VIDEO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 人脸/头部检测（算法抓脸队列）
FACE_CAPTURE_MODEL_PATH = os.getenv(
    'FACE_CAPTURE_MODEL_PATH',
    os.path.join(_VIDEO_ROOT, 'face_det.onnx'),
)
FACE_CAPTURE_CLASS_NAMES = {0: 'face'}

# 专用人脸检测（SCRFD 10G，输出人脸框 + 五点关键点）
FACE_DETECT_MODEL_PATH = os.getenv(
    'FACE_DETECT_MODEL_PATH',
    os.path.join(_VIDEO_ROOT, 'scrfd_10g.onnx'),
)

# 人脸特征提取（1:N 匹配，InsightFace ArcFace ONNX）
FACE_MATCH_MODEL_PATH = os.getenv(
    'FACE_MATCH_MODEL_PATH',
    os.path.join(_VIDEO_ROOT, 'face_rec.onnx'),
)
