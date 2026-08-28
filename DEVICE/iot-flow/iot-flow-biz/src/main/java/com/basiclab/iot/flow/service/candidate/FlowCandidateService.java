package com.basiclab.iot.flow.service.candidate;

import com.basiclab.iot.flow.framework.flowable.core.TaskCandidateConf;

import java.util.List;

/**
 * 候选人解析：策略 + 参数 -> 用户 ID 列表（去重、按 ID 排序保证稳定）
 */
public interface FlowCandidateService {

    /**
     * 解析候选人
     *
     * @param conf        节点候选人配置
     * @param startUserId 发起人
     * @param variables   流程变量（START_USER_SELECT 从 startUserSelectAssignees 读取）
     * @param nodeId      节点 ID（发起人自选变量键）
     */
    List<Long> resolve(TaskCandidateConf conf, Long startUserId, java.util.Map<String, Object> variables, String nodeId);

    /** 审批人为空兜底：返回应接手的用户（空 = 按自动通过/拒绝处理） */
    List<Long> resolveAssignEmpty(TaskCandidateConf conf, Long startUserId);

    /** 发起人相同审批策略（assignStartUserHandlerType）：对候选人中的发起人做替换/去重 */
    List<Long> applyAssignStartUserHandler(TaskCandidateConf conf, List<Long> candidateIds, Long startUserId);

    /** 校验用户有效并返回昵称映射（用于展示/记录冗余列） */
    java.util.Map<Long, String> getUserNicknameMap(java.util.Collection<Long> userIds);
}
