package com.basiclab.iot.infra.dal.pgsql.platformbranding;

import com.basiclab.iot.common.core.mapper.BaseMapperX;
import com.basiclab.iot.infra.dal.dataobject.platformbranding.PlatformBrandingDO;
import org.apache.ibatis.annotations.Mapper;

/**
 * 平台品牌配置 Mapper
 */
@Mapper
public interface PlatformBrandingMapper extends BaseMapperX<PlatformBrandingDO> {
}
