package com.basiclab.iot.message.service.impl;

import com.alibaba.fastjson.JSONObject;
import com.basiclab.iot.common.domain.AjaxResult;
import com.basiclab.iot.message.domain.entity.MessageConfig;
import com.basiclab.iot.message.mapper.MessageConfigMapper;
import com.basiclab.iot.message.service.MessageConfigService;
import org.apache.commons.collections4.CollectionUtils;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Component;

import java.util.List;
import java.util.UUID;

/**
 * 消息配置实现层impl
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 * @since 2024-07-18
 */
@Component
public class MessageConfigServiceImpl implements MessageConfigService {

    @Autowired
    private MessageConfigMapper messageConfigMapper;

    @Override
    public AjaxResult add(MessageConfig messageConfig) {
        MessageConfig messageConfig1 = messageConfigMapper.selectByMsgType(messageConfig.getMsgType());
        if(messageConfig1 != null){
            return AjaxResult.error(500, "新增失败，一个消息类型只能新增一个配置");
        }
        messageConfig.setId(UUID.randomUUID().toString());
        messageConfig.setCreateTime(System.currentTimeMillis());
        messageConfig.setCreatorId("25ea1da0-ed50-11ed-b15c-5face31d80ce");
        messageConfigMapper.add(messageConfig);
        return AjaxResult.success(messageConfig);
    }

    @Override
    public MessageConfig update(MessageConfig messageConfig) {
        messageConfigMapper.update(messageConfig);
        return messageConfig;
    }

    @Override
    public String delete(String id) {
        messageConfigMapper.delete(id);
        return id;
    }

    @Override
    public List<MessageConfig> query(MessageConfig messageConfig) {
        List<MessageConfig> messageConfigs = messageConfigMapper.selectList(messageConfig);
        for(MessageConfig messageConfig1 : CollectionUtils.emptyIfNull(messageConfigs)){
            JSONObject jsonObject = JSONObject.parseObject(messageConfig1.getConfiguration());
            messageConfig1.setConfigurationMap(jsonObject);
        }
        return messageConfigs;
    }

    @Override
    public MessageConfig queryById(String id) {
        MessageConfig messageConfig = messageConfigMapper.selectById(id);
        return messageConfig;
    }

    @Override
    public MessageConfig queryByMsgType(int msgType) {
        MessageConfig messageConfig = messageConfigMapper.selectByMsgType(msgType);
        JSONObject jsonObject = JSONObject.parseObject(messageConfig.getConfiguration());
        messageConfig.setConfigurationMap(jsonObject);
        return messageConfig;
    }
}
