package com.basiclab.iot.common.core.sender.local;

import com.basiclab.iot.common.core.sender.AbstractWebSocketMessageSender;
import com.basiclab.iot.common.core.sender.WebSocketMessageSender;
import com.basiclab.iot.common.core.session.WebSocketSessionManager;

/**
 * 本地的 {@link WebSocketMessageSender} 实现类
 *
 * 注意：仅仅适合单机场景！！！
 *
 * @author 深圳市深度智核科技有限责任公司
 */
public class LocalWebSocketMessageSender extends AbstractWebSocketMessageSender {

    public LocalWebSocketMessageSender(WebSocketSessionManager sessionManager) {
        super(sessionManager);
    }

}
