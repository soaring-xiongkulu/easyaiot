package com.basiclab.iot.message.service;

import com.basiclab.iot.message.domain.entity.TMsgSms;
import com.basiclab.iot.message.domain.model.vo.MessagePrepareVO;

import java.util.List;

public interface MessagePrepareService {

    MessagePrepareVO add(MessagePrepareVO messagePrepareVO);

    MessagePrepareVO update(MessagePrepareVO messagePrepareVO);

    String delete(int msgType,String id);

    List<?> query(MessagePrepareVO messagePrepareVO);

    TMsgSms querySmsByMsgId(String msgId);

}
