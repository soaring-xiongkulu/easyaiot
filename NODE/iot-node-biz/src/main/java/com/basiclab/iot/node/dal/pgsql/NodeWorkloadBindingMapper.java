package com.basiclab.iot.node.dal.pgsql;

import com.basiclab.iot.common.core.mapper.BaseMapperX;
import com.basiclab.iot.common.core.query.LambdaQueryWrapperX;
import com.basiclab.iot.node.dal.dataobject.NodeWorkloadBindingDO;
import org.apache.ibatis.annotations.Mapper;

import java.util.List;

@Mapper
public interface NodeWorkloadBindingMapper extends BaseMapperX<NodeWorkloadBindingDO> {

    default NodeWorkloadBindingDO selectByWorkload(String workloadType, String workloadId) {
        return selectOne(NodeWorkloadBindingDO::getWorkloadType, workloadType,
                NodeWorkloadBindingDO::getWorkloadId, workloadId);
    }

    default List<NodeWorkloadBindingDO> selectRunningByNodeId(Long nodeId) {
        return selectList(new LambdaQueryWrapperX<NodeWorkloadBindingDO>()
                .eq(NodeWorkloadBindingDO::getNodeId, nodeId)
                .eq(NodeWorkloadBindingDO::getStatus, "running"));
    }

    default long countRunningByNodeId(Long nodeId) {
        return selectCount(new LambdaQueryWrapperX<NodeWorkloadBindingDO>()
                .eq(NodeWorkloadBindingDO::getNodeId, nodeId)
                .eq(NodeWorkloadBindingDO::getStatus, "running"));
    }

}
