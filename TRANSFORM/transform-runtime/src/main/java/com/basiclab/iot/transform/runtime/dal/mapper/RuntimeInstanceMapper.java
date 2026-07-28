package com.basiclab.iot.transform.runtime.dal.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.basiclab.iot.transform.runtime.dal.dataobject.RuntimeInstanceDO;
import org.apache.ibatis.annotations.Mapper;

@Mapper
public interface RuntimeInstanceMapper extends BaseMapper<RuntimeInstanceDO> {
}
