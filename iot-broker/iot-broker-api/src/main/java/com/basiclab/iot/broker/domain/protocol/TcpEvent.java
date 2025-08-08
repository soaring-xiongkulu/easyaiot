package com.basiclab.iot.broker.domain.protocol;

/**
 * -----------------------------------------------------------------------------
 * File Name: TcpEvent
 * -----------------------------------------------------------------------------
 * Description:
 * Tcp事件
 * -----------------------------------------------------------------------------
 *
 * @author EasyAIoT
 * @version 1.0
 * -----------------------------------------------------------------------------
 * Revision History:
 * Date         Author          Version     Description
 * --------      --------     -------   --------------------
 * 2024/3/11       basiclab        1.0        Initial creation
 * -----------------------------------------------------------------------------
 * @email andywebjava@163.com
 * @date 2024/3/11 15:10
 */
public class TcpEvent extends ProtocolEvent {
    public TcpEvent(Object source, String message) {
        super(source, message);
    }
}