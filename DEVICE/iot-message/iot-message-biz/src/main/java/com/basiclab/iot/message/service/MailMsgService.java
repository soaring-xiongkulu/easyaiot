package com.basiclab.iot.message.service;

import com.github.pagehelper.PageInfo;
import com.basiclab.iot.message.domain.entity.TMsgMail;

public interface MailMsgService {

    TMsgMail add(TMsgMail tMsgMail);

    TMsgMail update(TMsgMail tMsgMail);

    String delete(String id);

    PageInfo<TMsgMail> query(int pageNum,int pageSize,TMsgMail tMsgMail);

    TMsgMail queryById(String id);

}
