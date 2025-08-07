package com.basiclab.iot.infra;

import com.basiclab.iot.common.annotation.EnableCustomSwagger2;
import com.basiclab.iot.common.annotations.EnableCustomConfig;
import com.basiclab.iot.common.annotations.EnableRyFeignClients;
import lombok.extern.slf4j.Slf4j;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.web.bind.annotation.CrossOrigin;

/**
 * 项目的启动类
 * <p>
 * @author EasyAIoT
 */
@Slf4j
@EnableCustomConfig
@EnableCustomSwagger2
@EnableRyFeignClients
@CrossOrigin(origins = "*", maxAge = 3600)
@SpringBootApplication(scanBasePackages = {"com.basiclab.iot"})
public class InfraServerApplication {

    public static void main(String[] args) {
        SpringApplication.run(InfraServerApplication.class, args);
    }
}
