package com.basiclab.iot.node.dal.pgsql;

import com.basiclab.iot.common.core.mapper.BaseMapperX;
import com.basiclab.iot.common.core.query.LambdaQueryWrapperX;
import com.basiclab.iot.common.domain.PageResult;
import com.basiclab.iot.node.dal.dataobject.NodeStorageOpLogDO;
import com.basiclab.iot.node.domain.vo.NodeStorageOpLogPageReqVO;
import org.apache.ibatis.annotations.Mapper;

@Mapper
public interface NodeStorageOpLogMapper extends BaseMapperX<NodeStorageOpLogDO> {

    default PageResult<NodeStorageOpLogDO> selectPage(NodeStorageOpLogPageReqVO reqVO) {
        return selectPage(reqVO, new LambdaQueryWrapperX<NodeStorageOpLogDO>()
                .eqIfPresent(NodeStorageOpLogDO::getNodeId, reqVO.getNodeId())
                .eqIfPresent(NodeStorageOpLogDO::getOpType, reqVO.getOpType())
                .orderByDesc(NodeStorageOpLogDO::getCreateTime));
    }

    default long countByNodeId(Long nodeId) {
        return selectCount(NodeStorageOpLogDO::getNodeId, nodeId);
    }
}
