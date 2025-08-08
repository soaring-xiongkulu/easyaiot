package com.basiclab.iot.common.config;

import com.basiclab.iot.common.core.rpc.TenantRequestInterceptor;
import com.basiclab.iot.system.api.tenant.TenantApi;
import org.springframework.boot.autoconfigure.AutoConfiguration;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.cloud.openfeign.EnableFeignClients;
import org.springframework.context.annotation.Bean;

@AutoConfiguration
@ConditionalOnProperty(prefix = "iot.tenant", value = "enable", matchIfMissing = true) // 允许使用 iot.tenant.enable=false 禁用多租户
@EnableFeignClients(clients = TenantApi.class) // 主要是引入相关的 API 服务
public class YudaoTenantRpcAutoConfiguration {

    @Bean
    public TenantRequestInterceptor tenantRequestInterceptor() {
        return new TenantRequestInterceptor();
    }

}
