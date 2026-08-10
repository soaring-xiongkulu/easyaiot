package com.basiclab.iot.video;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

/**
 * VIDEO Java candidate 入口（Phase -1 最小壳）。
 * <p>刻意不使用 {@code @EnableCustomConfig}，避免 Phase -1 拉起 DB / 租户等全家桶依赖。</p>
 */
@SpringBootApplication(scanBasePackages = "com.basiclab.iot.video")
public class VideoServerApplication {

    public static void main(String[] args) {
        SpringApplication.run(VideoServerApplication.class, args);
    }
}
