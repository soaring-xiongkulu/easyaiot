package com.basiclab.iot.device.dal.pgsql.ota;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.basiclab.iot.device.dal.dataobject.DmDeviceVersionPo;
import com.basiclab.iot.device.domain.ota.qo.DmDeviceVersionPageQo;
import com.basiclab.iot.device.domain.ota.vo.DmDeviceVersionVo;
import org.apache.ibatis.annotations.Mapper;

import java.util.List;

/**
 * 设备版本档案 Mapper
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Mapper
public interface DmDeviceVersionMapper extends BaseMapper<DmDeviceVersionPo> {

    /**
     * 设备版本档案分页查询（联版本包名称）
     */
    List<DmDeviceVersionVo> getVersionPageList(DmDeviceVersionPageQo query);
}
