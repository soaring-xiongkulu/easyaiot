package com.basiclab.iot.system.framework.rpc.config;

import com.basiclab.iot.infra.api.file.FileApi;
import com.basiclab.iot.infra.api.websocket.WebSocketSenderApi;
import org.springframework.cloud.openfeign.EnableFeignClients;
import org.springframework.context.annotation.Configuration;

@Configuration(proxyBeanMethods = false)
@EnableFeignClients(clients = {FileApi.class, WebSocketSenderApi.class})
public class RpcConfiguration {
}
