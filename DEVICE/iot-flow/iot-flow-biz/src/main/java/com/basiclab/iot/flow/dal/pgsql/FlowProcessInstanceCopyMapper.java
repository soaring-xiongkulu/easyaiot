package com.basiclab.iot.flow.dal.pgsql;

import com.basiclab.iot.common.core.mapper.BaseMapperX;
import com.basiclab.iot.common.core.query.LambdaQueryWrapperX;
import com.basiclab.iot.common.domain.PageParam;
import com.basiclab.iot.common.domain.PageResult;
import com.basiclab.iot.flow.dal.dataobject.FlowProcessInstanceCopyDO;
import org.apache.ibatis.annotations.Mapper;

/**
 * 流程抄送记录 Mapper
 */
@Mapper
public interface FlowProcessInstanceCopyMapper extends BaseMapperX<FlowProcessInstanceCopyDO> {

    default PageResult<FlowProcessInstanceCopyDO> selectPageByUserId(PageParam pageParam, Long userId,
                                                                     String processInstanceName) {
        return selectPage(pageParam, new LambdaQueryWrapperX<FlowProcessInstanceCopyDO>()
                .eq(FlowProcessInstanceCopyDO::getUserId, userId)
                .likeIfPresent(FlowProcessInstanceCopyDO::getProcessInstanceName, processInstanceName)
                .orderByDesc(FlowProcessInstanceCopyDO::getId));
    }

    default FlowProcessInstanceCopyDO selectByInstanceAndUser(String processInstanceId, Long userId) {
        return selectOne(new LambdaQueryWrapperX<FlowProcessInstanceCopyDO>()
                .eq(FlowProcessInstanceCopyDO::getProcessInstanceId, processInstanceId)
                .eq(FlowProcessInstanceCopyDO::getUserId, userId));
    }

}
