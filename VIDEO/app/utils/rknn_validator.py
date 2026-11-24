"""
RKNN 模型文件基础校验。

RKNN-Toolkit2 生成的模型以 RKNN/RKN1 魔数开头；这里只做文件头与大小校验，
1 输入 / 9 输出 INT8 等硬件契约由 RK3588 运行时在加载模型时强制校验。
"""
import os

_RKNN_MAGICS = (b'RKNN', b'RKN1')
_MIN_RKNN_FILE_SIZE = 16


def validate_rknn_model(model_path: str) -> dict:
    """校验 RKNN 文件头，返回格式、魔数与文件大小。"""
    if not model_path or not os.path.isfile(model_path):
        raise ValueError('RKNN 模型文件不存在')

    size = os.path.getsize(model_path)
    if size < _MIN_RKNN_FILE_SIZE:
        raise ValueError('RKNN 模型文件过小，可能不完整')

    with open(model_path, 'rb') as file_obj:
        magic = file_obj.read(4)
    if magic not in _RKNN_MAGICS:
        raise ValueError('不是有效的 RKNN 模型文件（缺少 RKNN/RKN1 文件头）')

    return {
        'format': 'rknn',
        'magic': magic.decode('ascii'),
        'size': size,
    }
