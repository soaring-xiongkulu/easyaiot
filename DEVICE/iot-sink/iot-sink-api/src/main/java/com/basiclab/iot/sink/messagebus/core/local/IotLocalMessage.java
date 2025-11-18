package com.basiclab.iot.sink.messagebus.core.local;

import lombok.AllArgsConstructor;
import lombok.Data;

/**
 * IotLocalMessage
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Data
@AllArgsConstructor
public class IotLocalMessage {

    private String topic;

    private Object message;

}
