package com.basiclab.iot.device.dal.mysql.device_topic;

import com.basiclab.iot.device.dal.dataobject.device_topic.DeviceTopicDO;
import com.basiclab.iot.common.domain.PageResult;
import com.basiclab.iot.common.mybatis.core.query.LambdaQueryWrapperX;
import com.basiclab.iot.common.mybatis.core.mapper.BaseMapperX;
import org.apache.ibatis.annotations.Mapper;
import com.basiclab.iot.device.controller.admin.device_topic.vo.*;

/**
 * 设备Topic数据 Mapper
 *
 * @author BasicLab
 */
@Mapper
public interface DeviceTopicMapper extends BaseMapperX<DeviceTopicDO> {

    default PageResult<DeviceTopicDO> selectPage(DeviceTopicPageReqVO reqVO) {
        return selectPage(reqVO, new LambdaQueryWrapperX<DeviceTopicDO>()
                .eqIfPresent(DeviceTopicDO::getDid, reqVO.getDid())
                .eqIfPresent(DeviceTopicDO::getType, reqVO.getType())
                .eqIfPresent(DeviceTopicDO::getTopic, reqVO.getTopic())
                .eqIfPresent(DeviceTopicDO::getPublisher, reqVO.getPublisher())
                .eqIfPresent(DeviceTopicDO::getSubscriber, reqVO.getSubscriber())
                .eqIfPresent(DeviceTopicDO::getCreateBy, reqVO.getCreateBy())
                .betweenIfPresent(DeviceTopicDO::getCreateTime, reqVO.getCreateTime())
                .eqIfPresent(DeviceTopicDO::getUpdateBy, reqVO.getUpdateBy())
                .eqIfPresent(DeviceTopicDO::getRemark, reqVO.getRemark())
                .orderByDesc(DeviceTopicDO::getId));
    }

}