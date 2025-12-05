package com.basiclab.iot.system.framework.rpc.config;

import com.basiclab.iot.infra.api.file.FileApi;
import com.basiclab.iot.infra.api.websocket.WebSocketSenderApi;
import com.basiclab.iot.system.api.mail.MailTemplateApi;
import com.basiclab.iot.system.api.notify.NotifyTemplateApi;
import org.springframework.cloud.openfeign.EnableFeignClients;
import org.springframework.context.annotation.Configuration;

/**
 * RpcConfiguration
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Configuration(proxyBeanMethods = false)
@EnableFeignClients(clients = {FileApi.class, WebSocketSenderApi.class, NotifyTemplateApi.class, MailTemplateApi.class})
public class RpcConfiguration {
}
