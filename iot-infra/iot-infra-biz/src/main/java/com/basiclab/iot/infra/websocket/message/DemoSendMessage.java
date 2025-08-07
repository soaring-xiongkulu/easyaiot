package com.basiclab.iot.infra.websocket.message;

import lombok.Data;

/**
 * 示例：client -> server 发送消息
 *
 * @author 安徽上洲智能科技
 */
@Data
public class DemoSendMessage {

    /**
     * 发送给谁
     *
     * 如果为空，说明发送给所有人
     */
    private Long toUserId;
    /**
     * 内容
     */
    private String text;

}
