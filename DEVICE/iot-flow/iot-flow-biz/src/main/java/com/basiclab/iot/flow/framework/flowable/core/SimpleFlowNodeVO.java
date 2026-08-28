package com.basiclab.iot.flow.framework.flowable.core;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import lombok.Data;

import java.util.List;

/**
 * Simple 设计器节点树（前端 SimpleFlowNode JSON 的 Java 镜像，字段按需裁剪）
 *
 * 单链表结构：root(START_USER_NODE) -> childNode -> ... ；分支节点用 conditionNodes 横向展开。
 */
@Data
@JsonIgnoreProperties(ignoreUnknown = true)
public class SimpleFlowNodeVO {

    private String id;
    private Integer type;
    private String name;
    private String showText;
    private SimpleFlowNodeVO childNode;
    private List<SimpleFlowNodeVO> conditionNodes;

    // ---------- 审批节点（USER_TASK） ----------
    private Integer approveType;
    private Integer candidateStrategy;
    /** 候选人参数（逗号分隔 ID） */
    private String candidateParam;
    private Integer approveMethod;
    /** 会签通过比例（百分比） */
    private Integer approveRatio;
    private Boolean reasonRequire;
    private TimeoutHandlerVO timeoutHandler;
    private RejectHandlerVO rejectHandler;
    private AssignEmptyHandlerVO assignEmptyHandler;
    private Integer assignStartUserHandlerType;

    // ---------- 条件节点（CONDITION_NODE 的 conditionSetting） ----------
    private ConditionSettingVO conditionSetting;

    // ---------- 延迟器（DELAY_TIMER） ----------
    private DelaySettingVO delaySetting;

    // ---------- 抄送节点（COPY_TASK，复用候选人策略字段） ----------

    @Data
    @JsonIgnoreProperties(ignoreUnknown = true)
    public static class TimeoutHandlerVO {
        private Boolean enable;
        private Integer type;
        /** ISO8601 时长，如 PT1H30M */
        private String timeDuration;
        private Integer maxRemindCount;
    }

    @Data
    @JsonIgnoreProperties(ignoreUnknown = true)
    public static class RejectHandlerVO {
        private Integer type;
        private String returnNodeId;
    }

    @Data
    @JsonIgnoreProperties(ignoreUnknown = true)
    public static class AssignEmptyHandlerVO {
        private Integer type;
        private List<Long> userIds;
    }

    @Data
    @JsonIgnoreProperties(ignoreUnknown = true)
    public static class ConditionSettingVO {
        private Integer conditionType;
        private String conditionExpression;
        private ConditionGroupVO conditionGroups;
        private Boolean defaultFlow;
    }

    @Data
    @JsonIgnoreProperties(ignoreUnknown = true)
    public static class ConditionGroupVO {
        private Boolean and;
        private List<ConditionVO> conditions;
    }

    @Data
    @JsonIgnoreProperties(ignoreUnknown = true)
    public static class ConditionVO {
        private Boolean and;
        private List<ConditionRuleVO> rules;
    }

    @Data
    @JsonIgnoreProperties(ignoreUnknown = true)
    public static class ConditionRuleVO {
        private String leftSide;
        private String opCode;
        private String rightSide;
    }

    @Data
    @JsonIgnoreProperties(ignoreUnknown = true)
    public static class DelaySettingVO {
        /** 1 固定时长（ISO8601 duration）/ 2 固定日期（ISO8601 dateTime） */
        private Integer delayType;
        private String delayTime;
    }

    /** 解析入口：JSON 字符串 -> 节点树 */
    public static SimpleFlowNodeVO parse(String json) {
        if (json == null || json.isEmpty()) {
            return null;
        }
        return com.basiclab.iot.common.utils.json.JsonUtils.parseObject2(json, SimpleFlowNodeVO.class);
    }

    /** 收集树中全部节点（含分支内节点） */
    public void collect(List<SimpleFlowNodeVO> collector) {
        collector.add(this);
        if (conditionNodes != null) {
            for (SimpleFlowNodeVO branch : conditionNodes) {
                branch.collect(collector);
            }
        }
        if (childNode != null) {
            childNode.collect(collector);
        }
    }
}
