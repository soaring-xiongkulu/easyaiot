package com.basiclab.iot.device.dal.pgsql.ota;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.basiclab.iot.device.dal.dataobject.DmPackagePublishPo;
import org.apache.ibatis.annotations.Mapper;

/**
 * 发布记录 Mapper
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Mapper
public interface DmPackagePublishMapper extends BaseMapper<DmPackagePublishPo> {
}
