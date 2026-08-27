package com.basiclab.iot.device.service.ota;

import com.basiclab.iot.device.domain.ota.oo.DmDeviceVersionAddOo;
import com.basiclab.iot.device.domain.ota.oo.DmDeviceVersionEditOo;
import com.basiclab.iot.device.domain.ota.qo.DmDeviceVersionPageQo;
import com.basiclab.iot.device.domain.ota.vo.DmDeviceVersionVo;

import java.util.List;

/**
 * 设备版本档案服务
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
public interface DmDeviceVersionService {

    /**
     * 分页列表
     */
    List<DmDeviceVersionVo> list(DmDeviceVersionPageQo qo);

    /**
     * 新增档案
     */
    void create(DmDeviceVersionAddOo oo);

    /**
     * 编辑档案
     */
    void edit(DmDeviceVersionEditOo oo);

    /**
     * 删除档案
     */
    void delete(Long id);
}
