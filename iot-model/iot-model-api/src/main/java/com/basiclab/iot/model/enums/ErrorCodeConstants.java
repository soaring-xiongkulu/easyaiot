package com.basiclab.iot.model.enums;

import com.basiclab.iot.common.exception.ErrorCode;

/**
 * Model 字典类型的枚举类
 * model 系统，使用 1-003-000-000 段
 *
 * @author EasyAIoT
 */
public interface ErrorCodeConstants {

    ErrorCode MODEL_NOT_EXISTS = new ErrorCode(1_005_000_000, "模型不存在");
    ErrorCode MODEL_SERVER_NOT_EXISTS = new ErrorCode(1_005_001_000, "模型服务不存在");
    ErrorCode MODEL_SERVER_QUANTIFY_NOT_EXISTS = new ErrorCode(1_005_002_000, "模型量化服务不存在");
    ErrorCode MODEL_SERVER_TEST_NOT_EXISTS = new ErrorCode(1_005_003_000, "模型测试服务不存在");
    ErrorCode MODEL_SERVER_TEST_IMAGE_NOT_EXISTS = new ErrorCode(1_005_004_000, "模型测试图片不存在");
    ErrorCode MODEL_SERVER_TEST_VIDEO_NOT_EXISTS = new ErrorCode(1_005_005_000, "模型测试视频不存在");
    ErrorCode MODEL_SERVER_VIDEO_NOT_EXISTS = new ErrorCode(1_005_006_000, "模型服务视频不存在");
    ErrorCode MODEL_TYPE_NOT_EXISTS = new ErrorCode(1_005_007_000, "模型类型不存在");
}
