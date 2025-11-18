package com.basiclab.iot.dataset.config;

import io.minio.MinioClient;
import io.minio.UploadObjectArgs;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Slf4j
@Configuration
public class MinioConfig {

    // Minio配置
    @Value("${minio.endpoint}")
    private String minioEndpoint;
    @Value("${minio.access-key}")
    private String minioAccessKey;
    @Value("${minio.secret-key}")
    private String minioSecretKey;
    @Value("${minio.bucket}")
    private String minioBucket;

    /**
 * MinioConfig
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */

@Bean
    public MinioClient minioClient(){
        return MinioClient.builder()
                .endpoint(minioEndpoint)
                .credentials(minioAccessKey, minioSecretKey)
                .build();
    }
}
