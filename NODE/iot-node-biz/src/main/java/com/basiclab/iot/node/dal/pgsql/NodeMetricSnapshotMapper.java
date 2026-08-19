package com.basiclab.iot.node.dal.pgsql;

import com.basiclab.iot.common.core.mapper.BaseMapperX;
import com.basiclab.iot.common.core.query.LambdaQueryWrapperX;
import com.basiclab.iot.node.dal.dataobject.NodeMetricSnapshotDO;
import org.apache.ibatis.annotations.Mapper;

import java.time.LocalDateTime;
import java.util.Collection;
import java.util.Collections;
import java.util.List;

@Mapper
public interface NodeMetricSnapshotMapper extends BaseMapperX<NodeMetricSnapshotDO> {

    default NodeMetricSnapshotDO selectLatestByNodeId(Long nodeId) {
        return selectOne(new LambdaQueryWrapperX<NodeMetricSnapshotDO>()
                .eq(NodeMetricSnapshotDO::getNodeId, nodeId)
                .orderByDesc(NodeMetricSnapshotDO::getCollectedAt)
                .last("LIMIT 1"));
    }

    default List<NodeMetricSnapshotDO> selectByNodeIdsSince(Collection<Long> nodeIds, LocalDateTime since) {
        if (nodeIds == null || nodeIds.isEmpty()) {
            return Collections.emptyList();
        }
        return selectList(new LambdaQueryWrapperX<NodeMetricSnapshotDO>()
                .in(NodeMetricSnapshotDO::getNodeId, nodeIds)
                .ge(NodeMetricSnapshotDO::getCollectedAt, since)
                .orderByAsc(NodeMetricSnapshotDO::getCollectedAt));
    }

}
