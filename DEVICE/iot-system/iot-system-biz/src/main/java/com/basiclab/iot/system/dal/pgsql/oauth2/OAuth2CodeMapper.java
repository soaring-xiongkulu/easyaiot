package com.basiclab.iot.system.dal.pgsql.oauth2;

import com.basiclab.iot.common.core.mapper.BaseMapperX;
import com.basiclab.iot.system.dal.dataobject.oauth2.OAuth2CodeDO;
import org.apache.ibatis.annotations.Mapper;

@Mapper
public interface OAuth2CodeMapper extends BaseMapperX<OAuth2CodeDO> {

    default OAuth2CodeDO selectByCode(String code) {
        return selectOne(OAuth2CodeDO::getCode, code);
    }

}
