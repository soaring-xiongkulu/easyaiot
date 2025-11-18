package com.basiclab.iot.device.hooks;

import lombok.Getter;
import lombok.Setter;
import lombok.ToString;

import java.io.Serializable;
import java.util.Map;

/**
 * DisconnectedHook
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@ToString
@Setter
@Getter
public class DisconnectedHook extends BaseHook implements Serializable {

    /**
     * 错误原因
     */

    private String reason;

    /**
     * 断开连接时间戳
     */
    private Long disconnectedAt;

    public DisconnectedHook(Map<String, Object> map) {
        super(map);
        this.setReason((String) map.get("reason"));
        this.setDisconnectedAt((Long) map.get("disconnected_at"));
    }
}