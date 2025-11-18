package com.basiclab.iot.device.service.device;

import com.basiclab.iot.device.domain.device.vo.DeviceServiceInvokeResponse;

/**
 * DeviceServiceInvokeResponseService
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
public interface DeviceServiceInvokeResponseService {

    /**
     * 保存服务调用响应
     *
     * @param response 响应数据
     * @return 保存的记录
     */
    DeviceServiceInvokeResponse save(DeviceServiceInvokeResponse response);

    /**
     * 根据消息ID查询
     *
     * @param messageId 消息ID
     * @return 响应数据
     */
    DeviceServiceInvokeResponse getByMessageId(String messageId);
}

