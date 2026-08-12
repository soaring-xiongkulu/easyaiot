package com.basiclab.iot.node.dal.pgsql;

import com.baomidou.mybatisplus.annotation.InterceptorIgnore;
import com.basiclab.iot.common.core.mapper.BaseMapperX;
import com.basiclab.iot.common.core.query.LambdaQueryWrapperX;
import com.basiclab.iot.node.dal.dataobject.NfsClusterDO;
import org.apache.ibatis.annotations.Mapper;

import java.util.List;

@Mapper
@InterceptorIgnore(tenantLine = "true")
public interface NfsClusterMapper extends BaseMapperX<NfsClusterDO> {

    default NfsClusterDO selectByLaneKey(String laneKey) {
        return selectOne(new LambdaQueryWrapperX<NfsClusterDO>()
                .eq(NfsClusterDO::getLaneKey, laneKey)
                .last("LIMIT 1"));
    }

    default NfsClusterDO selectActive() {
        return selectOne(new LambdaQueryWrapperX<NfsClusterDO>()
                .eq(NfsClusterDO::getIsActive, true)
                .last("LIMIT 1"));
    }

    default List<NfsClusterDO> selectAllActiveRows() {
        return selectList(new LambdaQueryWrapperX<NfsClusterDO>()
                .orderByDesc(NfsClusterDO::getIsActive)
                .orderByAsc(NfsClusterDO::getId));
    }
}
