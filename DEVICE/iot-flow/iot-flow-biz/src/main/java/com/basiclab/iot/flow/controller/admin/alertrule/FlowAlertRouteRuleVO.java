package com.basiclab.iot.flow.controller.admin.alertrule;

import com.basiclab.iot.flow.dal.dataobject.FlowAlertRouteRuleDO;
import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

import javax.validation.constraints.NotEmpty;
import javax.validation.constraints.NotNull;
import java.io.Serializable;
import java.time.LocalDateTime;
import java.util.List;

/**
 * 告警路由规则 VO（与前端 FlowAlertRouteRuleVO 对齐）
 */
@Schema(description = "管理后台 - 告警路由规则 VO")
@Data
public class FlowAlertRouteRuleVO implements Serializable {

    private static final long serialVersionUID = 1L;

    private Long id;
    @NotEmpty(message = "规则名称不能为空")
    private String ruleName;
    /** 优先级，大者先匹配 */
    private Integer priority;
    /** 命中后发起的流程标识（流程定义 key） */
    @NotEmpty(message = "流程标识不能为空")
    private String processDefinitionKey;
    /** 匹配条件（空数组 = 匹配全部） */
    private List<MatchCondition> matchConditions;
    /** 去重窗口（秒） */
    private Integer dedupWindowSeconds;
    /** 是否启用 */
    private Boolean enabled;
    /** 触发流程的虚拟发起人（空则系统账号 1） */
    private Long startUserId;
    private String remark;
    private LocalDateTime createTime;

    @Schema(description = "匹配条件")
    @Data
    public static class MatchCondition implements Serializable {

        private static final long serialVersionUID = 1L;

        /** 告警快照字段：object/event/taskType/taskId/taskName/deviceId/deviceName/nodeId/edgeNodeId 等 */
        private String field;
        /** 操作符：EQ / NE / IN / PREFIX / REGEX */
        private String op;
        private String value;

    }

    public FlowAlertRouteRuleDO toDO() {
        FlowAlertRouteRuleDO rule = new FlowAlertRouteRuleDO();
        rule.setId(id);
        rule.setRuleName(ruleName);
        rule.setPriority(priority == null ? 0 : priority);
        rule.setProcessDefinitionKey(processDefinitionKey);
        rule.setMatchConditions(toJson(matchConditions));
        rule.setDedupWindowSeconds(dedupWindowSeconds == null ? 0 : dedupWindowSeconds);
        rule.setEnabled(enabled == null ? Boolean.TRUE : enabled);
        rule.setStartUserId(startUserId);
        rule.setRemark(remark);
        return rule;
    }

    public static FlowAlertRouteRuleVO of(FlowAlertRouteRuleDO rule) {
        if (rule == null) {
            return null;
        }
        FlowAlertRouteRuleVO vo = new FlowAlertRouteRuleVO();
        vo.setId(rule.getId());
        vo.setRuleName(rule.getRuleName());
        vo.setPriority(rule.getPriority());
        vo.setProcessDefinitionKey(rule.getProcessDefinitionKey());
        vo.setMatchConditions(fromJson(rule.getMatchConditions()));
        vo.setDedupWindowSeconds(rule.getDedupWindowSeconds());
        vo.setEnabled(rule.getEnabled());
        vo.setStartUserId(rule.getStartUserId());
        vo.setRemark(rule.getRemark());
        vo.setCreateTime(rule.getCreateTime());
        return vo;
    }

    private static String toJson(List<MatchCondition> conditions) {
        return conditions == null ? "[]" : com.basiclab.iot.common.utils.json.JsonUtils.toJsonString(conditions);
    }

    private static List<MatchCondition> fromJson(String json) {
        if (json == null || json.isEmpty()) {
            return List.of();
        }
        return com.basiclab.iot.common.utils.json.JsonUtils.parseArray(json, MatchCondition.class);
    }

}
