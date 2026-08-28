package com.basiclab.iot.flow;

import com.basiclab.iot.common.annotation.EnableCustomSwagger2;
import com.basiclab.iot.common.annotations.EnableCustomConfig;
import com.basiclab.iot.common.annotations.EnableRyFeignClients;
import lombok.extern.slf4j.Slf4j;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.web.bind.annotation.CrossOrigin;

/**
 * FLOW 工作流服务启动入口
 *
 * 与其它服务一致：网关 TokenAuthenticationFilter 透传 login-user，
 * 控制器统一挂在 {@code **.controller.admin.**} 包下自动补 /admin-api 前缀。
 */
@EnableCustomConfig
@EnableCustomSwagger2
@EnableRyFeignClients
@CrossOrigin(origins = "*", maxAge = 3600)
@Slf4j
@SpringBootApplication(scanBasePackages = {"com.basiclab.iot"})
public class FlowServerApplication {

    public static void main(String[] args) {
        SpringApplication.run(FlowServerApplication.class, args);
    }

}
