package com.basiclab.iot.device.dal.pgsql.ota;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.basiclab.iot.device.dal.dataobject.DmPackageGrayScopePo;
import org.apache.ibatis.annotations.Mapper;

/**
 * 灰度范围 Mapper
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Mapper
public interface DmPackageGrayScopeMapper extends BaseMapper<DmPackageGrayScopePo> {
}
