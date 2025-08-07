package com.basiclab.iot.device.service.device_group;

import com.basiclab.iot.device.dal.dataobject.device_group.DeviceGroupDO;
import com.basiclab.iot.device.dal.mysql.device_group.DeviceGroupMapper;
import org.springframework.stereotype.Service;
import javax.annotation.Resource;
import org.springframework.validation.annotation.Validated;

import com.basiclab.iot.device.controller.admin.device_group.vo.*;
import com.basiclab.iot.common.domain.PageResult;
import com.basiclab.iot.common.utils.object.BeanUtils;


import static com.basiclab.iot.common.exception.util.ServiceExceptionUtil.exception;
import static com.basiclab.iot.device.enums.ErrorCodeConstants.*;

/**
 * 设备分组 Service 实现类
 *
 * @author BasicLab
 */
@Service
@Validated
public class DeviceGroupServiceImpl implements DeviceGroupService {

    @Resource
    private DeviceGroupMapper deviceGroupMapper;

    @Override
    public Long createGroup(DeviceGroupSaveReqVO createReqVO) {
        // 插入
        DeviceGroupDO group = BeanUtils.toBean(createReqVO, DeviceGroupDO.class);
        deviceGroupMapper.insert(group);
        // 返回
        return group.getId();
    }

    @Override
    public void updateGroup(DeviceGroupSaveReqVO updateReqVO) {
        // 校验存在
        validateGroupExists(updateReqVO.getId());
        // 更新
        DeviceGroupDO updateObj = BeanUtils.toBean(updateReqVO, DeviceGroupDO.class);
        deviceGroupMapper.updateById(updateObj);
    }

    @Override
    public void deleteGroup(Long id) {
        // 校验存在
        validateGroupExists(id);
        // 删除
        deviceGroupMapper.deleteById(id);
    }

    private void validateGroupExists(Long id) {
        if (deviceGroupMapper.selectById(id) == null) {
            throw exception(DEVICE_GROUP_NOT_EXISTS);
        }
    }

    @Override
    public DeviceGroupDO getGroup(Long id) {
        return deviceGroupMapper.selectById(id);
    }

    @Override
    public PageResult<DeviceGroupDO> getGroupPage(DeviceGroupPageReqVO pageReqVO) {
        return deviceGroupMapper.selectPage(pageReqVO);
    }

}