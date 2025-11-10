package com.basiclab.iot.dataset.enums;

import com.basiclab.iot.common.exception.ErrorCode;

/**
 * Dataset 字典类型的枚举类
 * dataset 系统，使用 1-003-000-000 段
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
public interface ErrorCodeConstants {

    //数据集
    ErrorCode DATASET_NOT_EXISTS = new ErrorCode(1_004_000_000, "数据集不存在");
    ErrorCode DATASET_SPLIT_RATIO_INVALID = new ErrorCode(1_004_000_001, "数据集分割比例不合法");
    ErrorCode DATASET_ALLOCATED = new ErrorCode(1_004_000_001, "数据集已分配，请重置后再分配");
    //图片数据集
    ErrorCode DATASET_IMAGE_NOT_EXISTS = new ErrorCode(1_004_001_000, "图片数据集不存在");
    ErrorCode TOTAL_DATASET_PARTITION_MUST_100_PERCENT = new ErrorCode(1_004_001_001, "数据集划分比例总和必须为100%");
    ErrorCode FILE_UPLOAD_FAILED = new ErrorCode(1_004_001_002, "文件上传失败");
    ErrorCode INVALID_FILE_TYPE = new ErrorCode(1_004_001_003, "不支持的文件类型");
    ErrorCode FILE_SIZE_EXCEEDED = new ErrorCode(1_004_001_004, "文件大小超过限制");
    //数据集标签
    ErrorCode DATASET_TAG_NOT_EXISTS = new ErrorCode(1_004_002_000, "数据集标签不存在");
    ErrorCode DATASET_TAG_NUMBER_EXISTS = new ErrorCode(1_004_002_001, "数据集标签编号已经存在");
    //标注任务
    ErrorCode DATASET_TASK_NOT_EXISTS = new ErrorCode(1_004_003_000, "标注任务不存在");
    //标注任务结果
    ErrorCode DATASET_TASK_RESULT_NOT_EXISTS = new ErrorCode(1_004_004_000, "标注任务结果不存在");
    //标注任务用户
    ErrorCode DATASET_TASK_USER_NOT_EXISTS = new ErrorCode(1_004_005_000, "标注任务用户不存在");
    //视频数据集
    ErrorCode DATASET_VIDEO_NOT_EXISTS = new ErrorCode(1_004_006_000, "视频数据集不存在");
    //视频流帧捕获任务
    ErrorCode DATASET_FRAME_TASK_NOT_EXISTS = new ErrorCode(1_004_007_000, "视频流帧捕获任务不存在");
    //数据仓
    ErrorCode WAREHOUSE_NOT_EXISTS = new ErrorCode(1_004_008_000, "数据仓不存在");
    //数据仓数据集关联
    ErrorCode WAREHOUSE_DATASET_NOT_EXISTS = new ErrorCode(1_004_009_000, "数据仓数据集关联不存在");

}
