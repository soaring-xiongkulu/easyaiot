package com.basiclab.iot.message.service;

import com.basiclab.iot.message.domain.entity.TPushHistory;

import java.util.List;

public interface PushHistoryService {
    TPushHistory add(TPushHistory tPushHistory);

    List<TPushHistory> query(TPushHistory tPushHistory);
}
