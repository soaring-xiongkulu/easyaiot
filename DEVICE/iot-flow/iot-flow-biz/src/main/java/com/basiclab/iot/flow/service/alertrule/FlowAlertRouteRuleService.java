package com.basiclab.iot.flow.service.alertrule;

import com.basiclab.iot.common.domain.PageParam;
import com.basiclab.iot.common.domain.PageResult;
import com.basiclab.iot.flow.controller.admin.alertrule.FlowAlertRouteRuleVO;
import com.basiclab.iot.flow.dal.dataobject.FlowAlertRouteRuleDO;

import java.util.List;
import java.util.Map;

/**
 * 告警路由规则 Service 接口
 */
public interface FlowAlertRouteRuleService {

    Long createRule(FlowAlertRouteRuleVO reqVO);

    void updateRule(FlowAlertRouteRuleVO reqVO);

    void updateEnabled(Long id, Boolean enabled);

    void deleteRule(Long id);

    FlowAlertRouteRuleDO getRule(Long id);

    PageResult<FlowAlertRouteRuleDO> getRulePage(PageParam pageParam, String ruleName, Boolean enabled);

    List<FlowAlertRouteRuleDO> getEnabledRulesByPriority();

    /** 规则试匹配：返回命中的规则（未命中返回 null） */
    FlowAlertRouteRuleDO previewMatch(Map<String, Object> alertSnapshot);

    /** 按条件匹配告警快照：全部条件都命中才算命中 */
    boolean matches(FlowAlertRouteRuleDO rule, Map<String, Object> snapshot);

}
