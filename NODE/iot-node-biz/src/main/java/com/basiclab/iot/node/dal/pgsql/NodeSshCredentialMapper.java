package com.basiclab.iot.node.dal.pgsql;

import com.basiclab.iot.common.core.mapper.BaseMapperX;
import com.basiclab.iot.node.dal.dataobject.NodeSshCredentialDO;
import org.apache.ibatis.annotations.Mapper;

@Mapper
public interface NodeSshCredentialMapper extends BaseMapperX<NodeSshCredentialDO> {

    default NodeSshCredentialDO selectByNodeId(Long nodeId) {
        return selectOne(NodeSshCredentialDO::getNodeId, nodeId);
    }

}
