package com.basiclab.iot.message.service.impl;

import com.github.pagehelper.PageInfo;
import com.basiclab.iot.message.domain.entity.TMsgMail;
import com.basiclab.iot.message.mapper.TMsgMailMapper;
import com.basiclab.iot.message.service.MailMsgService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Component;

/**
 * 邮件消息实现层Impl
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 * @since 2024-07-18
 */
@Component
public class MailMsgServiceImpl implements MailMsgService {

    @Autowired
    private TMsgMailMapper tMsgMailMapper;


    @Override
    public TMsgMail add(TMsgMail tMsgMail) {
        return null;
    }

    @Override
    public TMsgMail update(TMsgMail tMsgMail) {
        return null;
    }

    @Override
    public String delete(String id) {
        return null;
    }

    @Override
    public PageInfo<TMsgMail> query(int pageNum, int pageSize, TMsgMail tMsgMail) {
        return null;
    }

    @Override
    public TMsgMail queryById(String id) {
        return null;
    }
}
