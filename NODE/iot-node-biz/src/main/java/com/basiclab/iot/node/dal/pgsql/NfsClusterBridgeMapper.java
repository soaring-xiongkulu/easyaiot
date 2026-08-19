package com.basiclab.iot.node.dal.pgsql;

import com.baomidou.mybatisplus.annotation.InterceptorIgnore;
import com.basiclab.iot.common.core.mapper.BaseMapperX;
import com.basiclab.iot.common.core.query.LambdaQueryWrapperX;
import com.basiclab.iot.node.dal.dataobject.NfsClusterBridgeDO;
import org.apache.ibatis.annotations.Mapper;

import java.util.List;

@Mapper
@InterceptorIgnore(tenantLine = "true")
public interface NfsClusterBridgeMapper extends BaseMapperX<NfsClusterBridgeDO> {

    default List<NfsClusterBridgeDO> selectBySourceClusterId(Long sourceClusterId) {
        return selectList(new LambdaQueryWrapperX<NfsClusterBridgeDO>()
                .eq(NfsClusterBridgeDO::getSourceClusterId, sourceClusterId)
                .orderByDesc(NfsClusterBridgeDO::getId));
    }

    default List<NfsClusterBridgeDO> selectEnabled() {
        return selectList(new LambdaQueryWrapperX<NfsClusterBridgeDO>()
                .eq(NfsClusterBridgeDO::getEnabled, true)
                .orderByAsc(NfsClusterBridgeDO::getId));
    }

    default List<NfsClusterBridgeDO> selectAllOrdered() {
        return selectList(new LambdaQueryWrapperX<NfsClusterBridgeDO>()
                .orderByDesc(NfsClusterBridgeDO::getId));
    }
}
