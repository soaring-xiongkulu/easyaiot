package com.basiclab.iot.flow.service.alertrule;

import com.basiclab.iot.common.domain.PageParam;
import com.basiclab.iot.common.domain.PageResult;
import com.basiclab.iot.common.exception.util.ServiceExceptionUtil;
import com.basiclab.iot.flow.controller.admin.alertrule.FlowAlertRouteRuleVO;
import com.basiclab.iot.flow.dal.dataobject.FlowAlertRouteRuleDO;
import com.basiclab.iot.flow.dal.pgsql.FlowAlertRouteRuleMapper;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import javax.annotation.Resource;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.regex.Pattern;

import static com.basiclab.iot.flow.enums.FlowErrorCodeConstants.ALERT_ROUTE_RULE_NOT_EXISTS;

/**
 * 告警路由规则 Service 实现类
 */
@Slf4j
@Service
public class FlowAlertRouteRuleServiceImpl implements FlowAlertRouteRuleService {

    @Resource
    private FlowAlertRouteRuleMapper routeRuleMapper;

    @Override
    public Long createRule(FlowAlertRouteRuleVO reqVO) {
        FlowAlertRouteRuleDO rule = reqVO.toDO();
        routeRuleMapper.insert(rule);
        return rule.getId();
    }

    @Override
    public void updateRule(FlowAlertRouteRuleVO reqVO) {
        getRule(reqVO.getId());
        routeRuleMapper.updateById(reqVO.toDO());
    }

    @Override
    public void updateEnabled(Long id, Boolean enabled) {
        getRule(id);
        FlowAlertRouteRuleDO rule = new FlowAlertRouteRuleDO();
        rule.setId(id);
        rule.setEnabled(enabled);
        routeRuleMapper.updateById(rule);
    }

    @Override
    public void deleteRule(Long id) {
        getRule(id);
        routeRuleMapper.deleteById(id);
    }

    @Override
    public FlowAlertRouteRuleDO getRule(Long id) {
        FlowAlertRouteRuleDO rule = routeRuleMapper.selectById(id);
        if (rule == null) {
            throw ServiceExceptionUtil.exception(ALERT_ROUTE_RULE_NOT_EXISTS);
        }
        return rule;
    }

    @Override
    public PageResult<FlowAlertRouteRuleDO> getRulePage(PageParam pageParam, String ruleName, Boolean enabled) {
        return routeRuleMapper.selectPage(pageParam, ruleName, enabled);
    }

    @Override
    public List<FlowAlertRouteRuleDO> getEnabledRulesByPriority() {
        return routeRuleMapper.selectListByEnabled(true);
    }

    @Override
    public FlowAlertRouteRuleDO previewMatch(Map<String, Object> alertSnapshot) {
        List<FlowAlertRouteRuleDO> rules = routeRuleMapper.selectListByEnabled(true);
        rules.sort((a, b) -> Integer.compare(b.getPriority() == null ? 0 : b.getPriority(),
                a.getPriority() == null ? 0 : a.getPriority()));
        for (FlowAlertRouteRuleDO rule : rules) {
            if (matches(rule, alertSnapshot)) {
                return rule;
            }
        }
        return null;
    }

    @Override
    public boolean matches(FlowAlertRouteRuleDO rule, Map<String, Object> snapshot) {
        List<FlowAlertRouteRuleVO.MatchCondition> conditions = FlowAlertRouteRuleVO.of(rule).getMatchConditions();
        if (conditions == null || conditions.isEmpty()) {
            return true;
        }
        for (FlowAlertRouteRuleVO.MatchCondition condition : conditions) {
            if (!matchCondition(condition, snapshot)) {
                return false;
            }
        }
        return true;
    }

    private boolean matchCondition(FlowAlertRouteRuleVO.MatchCondition condition, Map<String, Object> snapshot) {
        if (condition.getField() == null) {
            return false;
        }
        Object raw = snapshot.get(condition.getField());
        String actual = raw == null ? "" : String.valueOf(raw);
        String expected = condition.getValue() == null ? "" : condition.getValue();
        String op = condition.getOp() == null ? "EQ" : condition.getOp();
        try {
            return switch (op) {
                case "EQ" -> Objects.equals(actual, expected);
                case "NE" -> !Objects.equals(actual, expected);
                case "IN" -> expected.isEmpty() || List.of(expected.split(",")).stream()
                        .map(String::trim).anyMatch(item -> item.equals(actual));
                case "PREFIX" -> actual.startsWith(expected);
                case "REGEX" -> Pattern.compile(expected).matcher(actual).find();
                default -> {
                    log.warn("[matchCondition] 未支持的匹配操作符: {}", op);
                    yield false;
                }
            };
        }
        catch (Exception e) {
            log.warn("[matchCondition] 条件匹配异常, field={}, op={}, value={}", condition.getField(), op, expected, e);
            return false;
        }
    }

}
