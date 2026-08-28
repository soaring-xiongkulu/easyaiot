package com.basiclab.iot.flow.enums;

import com.basiclab.iot.common.exception.ErrorCode;

/**
 * FLOW 工作流错误码：1-021-xxx-xxx
 */
public interface FlowErrorCodeConstants {

    // ========== 分类 1-021-001 ==========
    ErrorCode CATEGORY_NOT_EXISTS = new ErrorCode(1_021_001_001, "流程分类不存在");
    ErrorCode CATEGORY_EXISTS_CODE = new ErrorCode(1_021_001_002, "流程分类编码已存在");
    ErrorCode CATEGORY_USED_BY_MODEL = new ErrorCode(1_021_001_003, "流程分类被流程模型引用，无法删除");

    // ========== 用户组 1-021-002 ==========
    ErrorCode USER_GROUP_NOT_EXISTS = new ErrorCode(1_021_002_001, "用户组不存在");

    // ========== 模型 1-021-003 ==========
    ErrorCode MODEL_NOT_EXISTS = new ErrorCode(1_021_003_001, "流程模型不存在");
    ErrorCode MODEL_KEY_EXISTS = new ErrorCode(1_021_003_002, "流程模型标识已存在");
    ErrorCode MODEL_DEPLOY_FAILED = new ErrorCode(1_021_003_003, "流程部署失败：{}");
    ErrorCode MODEL_SIMPLE_MODEL_INVALID = new ErrorCode(1_021_003_004, "流程设计不完整，请检查流程图");

    // ========== 定义 1-021-004 ==========
    ErrorCode PROCESS_DEFINITION_NOT_EXISTS = new ErrorCode(1_021_004_001, "流程定义不存在");

    // ========== 实例 1-021-005 ==========
    ErrorCode PROCESS_INSTANCE_NOT_EXISTS = new ErrorCode(1_021_005_001, "流程实例不存在");
    ErrorCode PROCESS_INSTANCE_CANCEL_FAIL_NOT_EXISTS = new ErrorCode(1_021_005_002, "流程实例不存在或已结束");
    ErrorCode PROCESS_INSTANCE_CANCEL_FAIL_NOT_OWNER = new ErrorCode(1_021_005_003, "只有发起人才能取消流程");
    ErrorCode PROCESS_INSTANCE_START_FAIL = new ErrorCode(1_021_005_004, "流程发起失败：{}");

    // ========== 任务 1-021-006 ==========
    ErrorCode TASK_NOT_EXISTS = new ErrorCode(1_021_006_001, "任务不存在");
    ErrorCode TASK_NOT_ASSIGNEE = new ErrorCode(1_021_006_002, "当前用户不是任务的审批人");
    ErrorCode TASK_ALREADY_FINISHED = new ErrorCode(1_021_006_003, "任务已完成或已取消");
    ErrorCode TASK_RETURN_TARGET_INVALID = new ErrorCode(1_021_006_004, "退回目标节点无效");
    ErrorCode TASK_WITHDRAW_FAIL = new ErrorCode(1_021_006_005, "任务撤回失败：下一节点已处理或流程已变动");

    // ========== 告警路由 1-021-007 ==========
    ErrorCode ALERT_ROUTE_RULE_NOT_EXISTS = new ErrorCode(1_021_007_001, "告警路由规则不存在");
    ErrorCode ALERT_TRIGGER_NO_MATCH = new ErrorCode(1_021_007_002, "告警未命中任何路由规则");
    ErrorCode ALERT_TRIGGER_DEFINITION_NOT_FOUND = new ErrorCode(1_021_007_003, "路由规则指向的流程定义不存在或未启用");

    // ========== 告警记录 1-021-008 ==========
    ErrorCode ALERT_RECORD_NOT_EXISTS = new ErrorCode(1_021_008_001, "告警处理记录不存在");
    ErrorCode ALERT_RECORD_DUPLICATE = new ErrorCode(1_021_008_002, "该告警已存在处理记录，请勿重复发起");

}
