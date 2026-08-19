package com.basiclab.iot.node.dal.pgsql;

import com.basiclab.iot.common.core.mapper.BaseMapperX;
import com.basiclab.iot.common.core.query.LambdaQueryWrapperX;
import com.basiclab.iot.node.dal.dataobject.NodeSentinelRemediateLogDO;
import org.apache.ibatis.annotations.Mapper;

import java.util.List;

@Mapper
public interface NodeSentinelRemediateLogMapper extends BaseMapperX<NodeSentinelRemediateLogDO> {

    default List<NodeSentinelRemediateLogDO> selectRecentByNodeId(Long nodeId, int limit) {
        return selectList(new LambdaQueryWrapperX<NodeSentinelRemediateLogDO>()
                .eq(NodeSentinelRemediateLogDO::getNodeId, nodeId)
                .orderByDesc(NodeSentinelRemediateLogDO::getCreateTime)
                .last("LIMIT " + Math.max(1, Math.min(limit, 200))));
    }
}
