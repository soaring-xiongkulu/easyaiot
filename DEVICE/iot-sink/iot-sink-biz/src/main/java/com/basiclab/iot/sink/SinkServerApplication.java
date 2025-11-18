package com.basiclab.iot.sink;



import com.basiclab.iot.common.annotation.EnableCustomSwagger2;
import com.basiclab.iot.common.annotations.EnableCustomConfig;
import com.basiclab.iot.common.annotations.EnableRyFeignClients;
import lombok.extern.slf4j.Slf4j;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.web.bind.annotation.CrossOrigin;

@EnableCustomConfig
@EnableCustomSwagger2
@EnableRyFeignClients
@CrossOrigin(origins = "*", maxAge = 3600)


/**
 * SinkServerApplication
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */

@Slf4j
@SpringBootApplication(scanBasePackages = {"com.basiclab.iot"})
public class SinkServerApplication {

    public static void main(String[] args) {
        SpringApplication.run(SinkServerApplication.class, args);
    }

}