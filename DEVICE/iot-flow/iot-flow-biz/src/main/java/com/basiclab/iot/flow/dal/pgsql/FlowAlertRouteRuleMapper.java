package com.basiclab.iot.flow.dal.pgsql;

import com.basiclab.iot.common.core.mapper.BaseMapperX;
import com.basiclab.iot.common.core.query.LambdaQueryWrapperX;
import com.basiclab.iot.common.domain.PageParam;
import com.basiclab.iot.common.domain.PageResult;
import com.basiclab.iot.flow.dal.dataobject.FlowAlertRouteRuleDO;
import org.apache.ibatis.annotations.Mapper;

import java.util.List;

/**
 * 告警路由规则 Mapper
 */
@Mapper
public interface FlowAlertRouteRuleMapper extends BaseMapperX<FlowAlertRouteRuleDO> {

    default PageResult<FlowAlertRouteRuleDO> selectPage(PageParam pageParam, String ruleName, Boolean enabled) {
        return selectPage(pageParam, new LambdaQueryWrapperX<FlowAlertRouteRuleDO>()
                .likeIfPresent(FlowAlertRouteRuleDO::getRuleName, ruleName)
                .eqIfPresent(FlowAlertRouteRuleDO::getEnabled, enabled)
                .orderByDesc(FlowAlertRouteRuleDO::getPriority)
                .orderByDesc(FlowAlertRouteRuleDO::getId));
    }

    default List<FlowAlertRouteRuleDO> selectListByEnabled(Boolean enabled) {
        return selectList(new LambdaQueryWrapperX<FlowAlertRouteRuleDO>()
                .eqIfPresent(FlowAlertRouteRuleDO::getEnabled, enabled)
                .orderByDesc(FlowAlertRouteRuleDO::getPriority));
    }

}
