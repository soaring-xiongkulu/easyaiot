package com.basiclab.iot.flow.framework.security.config;

import com.basiclab.iot.common.config.AuthorizeRequestsCustomizer;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.annotation.web.configurers.ExpressionUrlAuthorizationConfigurer;

/**
 * FLOW 安全配置（对齐 iot-visualize：服务内放行，认证由网关统一完成）
 */
@Configuration(proxyBeanMethods = false, value = "flowSecurityConfiguration")
public class SecurityConfiguration {

    @Bean("flowAuthorizeRequestsCustomizer")
    public AuthorizeRequestsCustomizer authorizeRequestsCustomizer() {
        return new AuthorizeRequestsCustomizer() {

            @Override
            public void customize(ExpressionUrlAuthorizationConfigurer<HttpSecurity>.ExpressionInterceptUrlRegistry registry) {
                // Swagger 接口文档
                registry.antMatchers("/v3/api-docs/**").permitAll()
                        .antMatchers("/swagger-ui.html").permitAll()
                        .antMatchers("/**").permitAll();
                // Spring Boot Actuator 的安全配置
                registry.antMatchers("/actuator").anonymous()
                        .antMatchers("/actuator/**").anonymous();
            }

        };
    }

}
