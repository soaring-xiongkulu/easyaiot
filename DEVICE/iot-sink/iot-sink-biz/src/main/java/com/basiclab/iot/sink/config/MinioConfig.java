package com.basiclab.iot.sink.config;

import io.minio.MinioClient;
import lombok.Data;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.util.StringUtils;

/**
 * MinIO配置类
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Data
@Configuration
@ConfigurationProperties(prefix = "minio")
public class MinioConfig {

    /**
     * MinIO服务地址（格式：http://host:port）
     */
    private String url;

    /**
     * MinIO下载地址
     */
    private String downloadUrl;

    /**
     * 访问密钥
     */
    private String accessKey;

    /**
     * 秘密密钥
     */
    private String secretKey;

    /**
     * 存储桶名称
     */
    private String bucketName;

    /**
     * 分块大小（MB）
     */
    private Integer chunk;

    /**
     * 分块合并大小
     */
    private Integer chunkSize;

    @Bean
    public MinioClient minioClient() {
        if (!StringUtils.hasText(url) || !StringUtils.hasText(accessKey) || !StringUtils.hasText(secretKey)) {
            throw new IllegalStateException("MinIO配置不完整，无法创建客户端。请检查配置文件中的 minio.url、minio.accessKey 和 minio.secretKey 配置项");
        }
        
        try {
            return MinioClient.builder()
                    .endpoint(url)
                    .credentials(accessKey, secretKey)
                    .build();
        } catch (Exception e) {
            throw new IllegalStateException("MinIO客户端创建失败: " + e.getMessage(), e);
        }
    }
}

