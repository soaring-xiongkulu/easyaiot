package com.basiclab.iot.broker.service;


import com.basiclab.iot.broker.domain.vo.PublishMessageRequestVO;
import com.basiclab.iot.common.exception.BaseException;

/**
 * -----------------------------------------------------------------------------
 * File Name: MqttBrokerService.java
 * -----------------------------------------------------------------------------
 * Description:
 * MqttBroker API
 * -----------------------------------------------------------------------------
 *
 * @author EasyAIoT
 * @version 1.0
 * -----------------------------------------------------------------------------
 * Revision History:
 * Date         Author          Version     Description
 * --------      --------     -------   --------------------
 * <p>
 * -----------------------------------------------------------------------------
 * @date 2023-10-31 19:43
 */
public interface MqttBrokerService {


    /**
     * Publishes a message to a specified topic and returns the content if successful.
     *
     * @param publishMessageRequestVO Object containing the required parameters for publishing.
     * @return The content of the published message.
     * @throws BaseException If the publishing fails.
     */
    String publishMessage(PublishMessageRequestVO publishMessageRequestVO);
}
