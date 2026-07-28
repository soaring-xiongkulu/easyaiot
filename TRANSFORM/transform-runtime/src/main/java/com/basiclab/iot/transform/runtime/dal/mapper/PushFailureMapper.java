package com.basiclab.iot.transform.runtime.dal.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.basiclab.iot.transform.runtime.dal.dataobject.PushFailureDO;
import org.apache.ibatis.annotations.Mapper;

@Mapper
public interface PushFailureMapper extends BaseMapper<PushFailureDO> {
}
