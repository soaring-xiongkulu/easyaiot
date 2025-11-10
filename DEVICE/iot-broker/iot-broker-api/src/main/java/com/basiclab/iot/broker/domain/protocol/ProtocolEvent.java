package com.basiclab.iot.broker.domain.protocol;

import org.springframework.context.ApplicationEvent;

/**
 * -----------------------------------------------------------------------------
 * File Name: ProtocolEvent
 * -----------------------------------------------------------------------------
 * Description:
 * 协议事件类
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
 * @date 2024/3/11 15:03
 */
public class ProtocolEvent extends ApplicationEvent {
    private final String message;

    public ProtocolEvent(Object source, String message) {
        super(source);
        this.message = message;
    }

    public String getMessage() {
        return message;
    }
}
