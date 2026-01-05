package com.genersoft.iot.vmp.framework.security.config;

import com.basiclab.iot.common.config.AuthorizeRequestsCustomizer;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.annotation.web.configurers.ExpressionUrlAuthorizationConfigurer;

/**
 * SecurityConfiguration
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */

@Configuration(proxyBeanMethods = false, value = "gb28181SecurityConfiguration")
public class SecurityConfiguration {

    @Bean("gb28181AuthorizeRequestsCustomizer")
    public AuthorizeRequestsCustomizer authorizeRequestsCustomizer() {
        return new AuthorizeRequestsCustomizer() {

            @Override
            public void customize(ExpressionUrlAuthorizationConfigurer<HttpSecurity>.ExpressionInterceptUrlRegistry registry) {
                // TODO BasicLab：这个每个项目都需要重复配置，得捉摸有没通用的方案
                // Swagger 接口文档
                registry.antMatchers("/v3/api-docs/**").permitAll() // 元数据
                        .antMatchers("/swagger-ui.html").permitAll() // Swagger UI
                        .antMatchers("/index/hook/**").permitAll()
                        .antMatchers("/api/play/uploadSnapshot").permitAll() // zlm hook
                        .antMatchers("/**").permitAll();
                // Druid 监控
                registry.antMatchers("/druid/**").anonymous();
                // Spring Boot Actuator 的安全配置
                registry.antMatchers("/actuator").anonymous()
                        .antMatchers("/actuator/**").anonymous();
                // Note: ApiConstants not available in gb28181 module, so RPC service config is omitted
                // If needed, create ApiConstants class in iot-gb28181-api module
            }

        };
    }

}

