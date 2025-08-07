package com.basiclab.iot.infra.framework.rpc.config;

import com.basiclab.iot.system.api.user.AdminUserApi;
import org.springframework.cloud.openfeign.EnableFeignClients;
import org.springframework.context.annotation.Configuration;

@Configuration(proxyBeanMethods = false)
@EnableFeignClients(clients = AdminUserApi.class)
public class RpcConfiguration {
}
