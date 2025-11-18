package com.basiclab.iot.device.service.device.impl;

import com.basiclab.iot.device.dal.pgsql.device.DeviceServiceInvokeResponseMapper;
import com.basiclab.iot.device.domain.device.vo.DeviceServiceInvokeResponse;
import com.basiclab.iot.device.service.device.DeviceServiceInvokeResponseService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;

/**
 * DeviceServiceInvokeResponseServiceImpl
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Slf4j
@Service
@RequiredArgsConstructor
@Transactional(rollbackFor = Exception.class)
public class DeviceServiceInvokeResponseServiceImpl implements DeviceServiceInvokeResponseService {

    private final DeviceServiceInvokeResponseMapper mapper;

    @Override
    public DeviceServiceInvokeResponse save(DeviceServiceInvokeResponse response) {
        if (response.getCreateTime() == null) {
            response.setCreateTime(LocalDateTime.now());
        }
        mapper.insert(response);
        log.debug("[save][保存服务调用响应成功，messageId: {}, deviceId: {}]",
                response.getMessageId(), response.getDeviceId());
        return response;
    }

    @Override
    public DeviceServiceInvokeResponse getByMessageId(String messageId) {
        return mapper.selectByMessageId(messageId);
    }
}

