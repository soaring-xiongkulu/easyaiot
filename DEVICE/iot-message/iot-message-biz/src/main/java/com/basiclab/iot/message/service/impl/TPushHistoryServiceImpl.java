package com.basiclab.iot.message.service.impl;

import com.basiclab.iot.message.domain.entity.TPushHistory;
import com.basiclab.iot.message.mapper.TPushHistoryMapper;
import com.basiclab.iot.message.service.PushHistoryService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Component;

import java.util.Date;
import java.util.List;
import java.util.UUID;

/**
 * 推送历史实现层Impl
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 * @since 2024-07-18
 */
@Component
public class TPushHistoryServiceImpl implements PushHistoryService {

    @Autowired
    private TPushHistoryMapper tPushHistoryMapper;

    @Override
    public TPushHistory add(TPushHistory tPushHistory) {
        tPushHistory.setId(UUID.randomUUID().toString());
        tPushHistory.setCreateTime(new Date());
        tPushHistoryMapper.insert(tPushHistory);
        return tPushHistory;
    }

    @Override
    public List<TPushHistory> query( TPushHistory tPushHistory) {
        return tPushHistoryMapper.selectByMsgType(tPushHistory.getMsgType(),tPushHistory.getMsgName());
    }
}
