package com.basiclab.iot.message;

import com.basiclab.iot.common.annotation.EnableCustomSwagger2;
import com.basiclab.iot.common.annotations.EnableCustomConfig;
import com.basiclab.iot.common.annotations.EnableRyFeignClients;
import lombok.extern.slf4j.Slf4j;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.scheduling.annotation.EnableAsync;
import org.springframework.web.bind.annotation.CrossOrigin;


@EnableCustomConfig
@EnableCustomSwagger2
@EnableRyFeignClients
@EnableAsync(proxyTargetClass = true)
@CrossOrigin(origins = "*", maxAge = 3600)
@Slf4j
@SpringBootApplication(scanBasePackages = {"com.basiclab.iot"})
public class MessageApplication {

    public static void main(String[] args) {
        SpringApplication.run(MessageApplication.class, args);
    }
}
