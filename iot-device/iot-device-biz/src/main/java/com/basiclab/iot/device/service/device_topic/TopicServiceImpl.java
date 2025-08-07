package com.basiclab.iot.device.service.device_topic;

import com.basiclab.iot.device.dal.dataobject.device_topic.DeviceTopicDO;
import com.basiclab.iot.device.dal.mysql.device_topic.DeviceTopicMapper;
import org.springframework.stereotype.Service;
import javax.annotation.Resource;
import org.springframework.validation.annotation.Validated;

import com.basiclab.iot.device.controller.admin.device_topic.vo.*;
import com.basiclab.iot.common.domain.PageResult;
import com.basiclab.iot.common.utils.object.BeanUtils;

import static com.basiclab.iot.device.enums.ErrorCodeConstants.DEVICE_TOPIC_NOT_EXISTS;
import static com.basiclab.iot.common.exception.util.ServiceExceptionUtil.exception;

/**
 * 设备Topic数据 Service 实现类
 *
 * @author BasicLab
 */
@Service
@Validated
public class TopicServiceImpl implements TopicService {

    @Resource
    private DeviceTopicMapper topicMapper;

    @Override
    public Long createTopic(DeviceTopicSaveReqVO createReqVO) {
        // 插入
        DeviceTopicDO topic = BeanUtils.toBean(createReqVO, DeviceTopicDO.class);
        topicMapper.insert(topic);
        // 返回
        return topic.getId();
    }

    @Override
    public void updateTopic(DeviceTopicSaveReqVO updateReqVO) {
        // 校验存在
        validateTopicExists(updateReqVO.getId());
        // 更新
        DeviceTopicDO updateObj = BeanUtils.toBean(updateReqVO, DeviceTopicDO.class);
        topicMapper.updateById(updateObj);
    }

    @Override
    public void deleteTopic(Long id) {
        // 校验存在
        validateTopicExists(id);
        // 删除
        topicMapper.deleteById(id);
    }

    private void validateTopicExists(Long id) {
        if (topicMapper.selectById(id) == null) {
            throw exception(DEVICE_TOPIC_NOT_EXISTS);
        }
    }

    @Override
    public DeviceTopicDO getTopic(Long id) {
        return topicMapper.selectById(id);
    }

    @Override
    public PageResult<DeviceTopicDO> getTopicPage(DeviceTopicPageReqVO pageReqVO) {
        return topicMapper.selectPage(pageReqVO);
    }

}