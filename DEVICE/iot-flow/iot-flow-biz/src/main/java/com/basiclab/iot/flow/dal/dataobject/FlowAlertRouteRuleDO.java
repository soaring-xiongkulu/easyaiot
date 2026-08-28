package com.basiclab.iot.flow.dal.dataobject;

import com.baomidou.mybatisplus.annotation.KeySequence;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import com.basiclab.iot.common.core.dataobject.BaseDO;
import lombok.Data;
import lombok.EqualsAndHashCode;

/**
 * 告警 → 流程 路由规则
 *
 * 告警链路与租户无关（告警来自 VIDEO 库），因此使用 BaseDO。
 */
@TableName("flow_alert_route_rule")
@KeySequence("flow_alert_route_rule_seq")
@Data
@EqualsAndHashCode(callSuper = true)
public class FlowAlertRouteRuleDO extends BaseDO {

    @TableId
    private Long id;
    /** 规则名称 */
    private String ruleName;
    /** 优先级，大者先匹配 */
    private Integer priority;
    /** 命中后发起的流程标识（流程定义 key） */
    private String processDefinitionKey;
    /** 匹配条件 JSON：[{field, op, value}]，空数组 = 匹配全部 */
    private String matchConditions;
    /** 去重窗口（秒）：同 告警对象+任务+事件 在窗口内只发起一次 */
    private Integer dedupWindowSeconds;
    /** 是否启用 */
    private Boolean enabled;
    /** 触发流程的虚拟发起人（为空则用系统管理员账号 1） */
    private Long startUserId;
    /** 备注 */
    private String remark;

}
