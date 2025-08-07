package com.basiclab.iot.device.dal.mysql.device_group;

import com.basiclab.iot.device.dal.dataobject.device_group.DeviceGroupDO;
import com.basiclab.iot.common.domain.PageResult;
import com.basiclab.iot.common.mybatis.core.query.LambdaQueryWrapperX;
import com.basiclab.iot.common.mybatis.core.mapper.BaseMapperX;
import org.apache.ibatis.annotations.Mapper;
import com.basiclab.iot.device.controller.admin.device_group.vo.*;

/**
 * 设备分组 Mapper
 *
 * @author BasicLab
 */
@Mapper
public interface DeviceGroupMapper extends BaseMapperX<DeviceGroupDO> {

    default PageResult<DeviceGroupDO> selectPage(DeviceGroupPageReqVO reqVO) {
        return selectPage(reqVO, new LambdaQueryWrapperX<DeviceGroupDO>()
                .likeIfPresent(DeviceGroupDO::getGroupName, reqVO.getGroupName())
                .eqIfPresent(DeviceGroupDO::getCreateBy, reqVO.getCreateBy())
                .betweenIfPresent(DeviceGroupDO::getCreateTime, reqVO.getCreateTime())
                .eqIfPresent(DeviceGroupDO::getUpdateBy, reqVO.getUpdateBy())
                .orderByDesc(DeviceGroupDO::getId));
    }

}