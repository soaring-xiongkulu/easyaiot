package com.basiclab.iot.broker.domain.protocol;

/**
 * -----------------------------------------------------------------------------
 * File Name: WebSocketEvent
 * -----------------------------------------------------------------------------
 * Description:
 * WebSocket事件
 * -----------------------------------------------------------------------------
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 * @version 1.0
 * -----------------------------------------------------------------------------
 * Revision History:
 * Date         Author          Version     Description
 * --------      --------     -------   --------------------
 * 2024/3/11       basiclab        1.0        Initial creation
 * -----------------------------------------------------------------------------
 * @email andywebjava@163.com
 * @date 2024/3/11 15:06
 */
public class WebSocketEvent extends ProtocolEvent {
    public WebSocketEvent(Object source, String message) {
        super(source, message);
    }
}
