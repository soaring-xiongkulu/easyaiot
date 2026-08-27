package com.basiclab.iot.device.service.ota.impl;

import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.basiclab.iot.common.exception.ServiceException;
import com.basiclab.iot.common.utils.JSONUtils;
import com.basiclab.iot.device.dal.dataobject.DmDeviceVersionPo;
import com.basiclab.iot.device.dal.pgsql.ota.DmDeviceVersionMapper;
import com.basiclab.iot.device.domain.ota.oo.DmDeviceVersionAddOo;
import com.basiclab.iot.device.domain.ota.oo.DmDeviceVersionEditOo;
import com.basiclab.iot.device.domain.ota.qo.DmDeviceVersionPageQo;
import com.basiclab.iot.device.domain.ota.vo.DmDeviceVersionVo;
import com.basiclab.iot.device.service.ota.DmDeviceVersionService;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import javax.annotation.Resource;
import java.util.List;

/**
 * 设备版本档案服务实现
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Service
@Slf4j
public class DmDeviceVersionServiceImpl extends ServiceImpl<DmDeviceVersionMapper, DmDeviceVersionPo>
        implements DmDeviceVersionService {

    @Override
    public List<DmDeviceVersionVo> list(DmDeviceVersionPageQo qo) {
        return baseMapper.getVersionPageList(qo);
    }

    @Override
    public void create(DmDeviceVersionAddOo oo) {
        DmDeviceVersionPo po = JSONUtils.copy(oo, DmDeviceVersionPo.class);
        baseMapper.insert(po);
    }

    @Override
    public void edit(DmDeviceVersionEditOo oo) {
        if (baseMapper.selectById(oo.getId()) == null) {
            throw new ServiceException("设备版本档案不存在");
        }
        DmDeviceVersionPo po = JSONUtils.copy(oo, DmDeviceVersionPo.class);
        baseMapper.updateById(po);
    }

    @Override
    public void delete(Long id) {
        baseMapper.deleteById(id);
    }
}
