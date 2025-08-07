package com.basiclab.iot.device.service.device;

import com.basiclab.iot.device.controller.admin.device.vo.Device;
import com.basiclab.iot.device.controller.admin.device.vo.DevicePageReqVO;
import com.basiclab.iot.device.controller.admin.device.vo.DeviceSaveReqVO;
import com.basiclab.iot.device.dal.dataobject.device.DeviceDO;
import com.basiclab.iot.device.dal.mysql.device.DeviceMapper;
import com.basiclab.iot.common.domain.PageResult;
import com.basiclab.iot.common.utils.object.BeanUtils;
import org.springframework.stereotype.Service;
import org.springframework.validation.annotation.Validated;

import javax.annotation.Resource;
import java.util.List;

import static com.basiclab.iot.device.enums.ErrorCodeConstants.DEVICE_NOT_EXISTS;
import static com.basiclab.iot.common.exception.util.ServiceExceptionUtil.exception;

/**
 * 设备 Service 实现类
 *
 * @author BasicLab
 */
@Service
@Validated
public class DeviceServiceImpl implements DeviceService {

    @Resource
    private DeviceMapper deviceMapper;

    @Override
    public List<Device> selectDeviceList(Device device) {
        return deviceMapper.selectDeviceList(device);
    }

    @Override
    public Device selectDeviceById(Long id) {
        return deviceMapper.selectDeviceById(id);
    }

    @Override
    public Long create(DeviceSaveReqVO createReqVO) {
        // 插入
        DeviceDO deviceDO = BeanUtils.toBean(createReqVO, DeviceDO.class);
        deviceMapper.insert(deviceDO);
        // 返回
        return deviceDO.getId();
    }

    @Override
    public void update(DeviceSaveReqVO updateReqVO) {
        // 校验存在
        validateExists(updateReqVO.getId());
        // 更新
        DeviceDO updateObj = BeanUtils.toBean(updateReqVO, DeviceDO.class);
        deviceMapper.updateById(updateObj);
    }

    @Override
    public void delete(Long id) {
        // 校验存在
        validateExists(id);
        // 删除
        deviceMapper.deleteById(id);
    }

    private void validateExists(Long id) {
        if (deviceMapper.selectById(id) == null) {
            throw exception(DEVICE_NOT_EXISTS);
        }
    }

    @Override
    public DeviceDO get(Long id) {
        return deviceMapper.selectById(id);
    }

    @Override
    public PageResult<DeviceDO> getPage(DevicePageReqVO pageReqVO) {
        return deviceMapper.selectPage(pageReqVO);
    }

}