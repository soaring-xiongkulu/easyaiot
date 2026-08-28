package com.basiclab.iot.flow.dal.pgsql;

import com.basiclab.iot.common.core.mapper.BaseMapperX;
import com.basiclab.iot.common.core.query.LambdaQueryWrapperX;
import com.basiclab.iot.common.domain.PageParam;
import com.basiclab.iot.common.domain.PageResult;
import com.basiclab.iot.flow.dal.dataobject.FlowUserGroupDO;
import org.apache.ibatis.annotations.Mapper;

import java.util.List;

/**
 * 审批用户组 Mapper
 */
@Mapper
public interface FlowUserGroupMapper extends BaseMapperX<FlowUserGroupDO> {

    default PageResult<FlowUserGroupDO> selectPage(PageParam pageParam, String name, Integer status) {
        return selectPage(pageParam, new LambdaQueryWrapperX<FlowUserGroupDO>()
                .likeIfPresent(FlowUserGroupDO::getName, name)
                .eqIfPresent(FlowUserGroupDO::getStatus, status)
                .orderByDesc(FlowUserGroupDO::getId));
    }

    default List<FlowUserGroupDO> selectSimpleList() {
        return selectList(new LambdaQueryWrapperX<FlowUserGroupDO>()
                .eq(FlowUserGroupDO::getStatus, 0)
                .orderByDesc(FlowUserGroupDO::getId));
    }

}
