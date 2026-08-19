package com.basiclab.iot.node.dal.pgsql;

import com.basiclab.iot.common.core.mapper.BaseMapperX;
import com.basiclab.iot.node.dal.dataobject.NodeSentinelSnapshotDO;
import org.apache.ibatis.annotations.Mapper;

@Mapper
public interface NodeSentinelSnapshotMapper extends BaseMapperX<NodeSentinelSnapshotDO> {
}
