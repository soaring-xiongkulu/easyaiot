package com.basiclab.iot.node.dal.pgsql;

import com.basiclab.iot.common.core.mapper.BaseMapperX;
import com.basiclab.iot.node.dal.dataobject.ControlPlanePeerDO;
import org.apache.ibatis.annotations.Mapper;

@Mapper
public interface ControlPlanePeerMapper extends BaseMapperX<ControlPlanePeerDO> {

    default ControlPlanePeerDO selectByApiBaseUrl(String apiBaseUrl) {
        return selectOne(ControlPlanePeerDO::getApiBaseUrl, apiBaseUrl);
    }

    default long countActivePeers() {
        return selectCount();
    }

}
