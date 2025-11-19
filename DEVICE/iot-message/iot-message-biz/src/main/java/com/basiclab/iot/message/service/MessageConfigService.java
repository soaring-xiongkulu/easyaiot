package com.basiclab.iot.message.service;


import com.basiclab.iot.common.domain.AjaxResult;
import com.basiclab.iot.message.domain.entity.MessageConfig;

import java.util.List;

public interface MessageConfigService {
    AjaxResult add(MessageConfig messageConfig);

    MessageConfig update(MessageConfig messageConfig);

    String delete(String id);

    List<MessageConfig> query(MessageConfig messageConfig);

    MessageConfig queryById(String id);

    MessageConfig queryByMsgType(int msgType);
}
