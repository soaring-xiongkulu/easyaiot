package com.basiclab.iot.dataset.config;

import io.minio.MinioClient;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.Primary;
import org.springframework.util.StringUtils;

import javax.annotation.PostConstruct;

/**
 * MinioConfig
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
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
     * 验证配置是否完整
     */
    @PostConstruct
    public void validateConfig() {
        if (!StringUtils.hasText(minioEndpoint)) {
            log.error("MinIO配置错误: endpoint 未配置");
            throw new IllegalStateException("MinIO配置错误: endpoint 未配置，请在配置文件中设置 minio.endpoint");
        }
        if (!StringUtils.hasText(minioAccessKey)) {
            log.error("MinIO配置错误: access-key 未配置");
            throw new IllegalStateException("MinIO配置错误: access-key 未配置，请在配置文件中设置 minio.access-key");
        }
        if (!StringUtils.hasText(minioSecretKey)) {
            log.error("MinIO配置错误: secret-key 未配置");
            throw new IllegalStateException("MinIO配置错误: secret-key 未配置，请在配置文件中设置 minio.secret-key");
        }
        if (!StringUtils.hasText(minioBucket)) {
            log.warn("MinIO配置警告: bucket 未配置，可能影响文件上传功能");
        }
        
        // 记录配置信息（隐藏敏感信息）
        log.info("MinIO配置加载成功 - endpoint: {}, accessKey: {}, bucket: {}", 
                minioEndpoint, 
                StringUtils.hasText(minioAccessKey) ? maskString(minioAccessKey) : "未配置",
                minioBucket);
    }

    /**
     * 掩码敏感字符串（只显示前3个字符）
     */
    private String maskString(String str) {
        if (str == null || str.length() <= 3) {
            return "***";
        }
        return str.substring(0, 3) + "***";
    }

    @Bean("minioClient")
    @Primary
    public MinioClient minioClient() {
        if (!StringUtils.hasText(minioEndpoint) || !StringUtils.hasText(minioAccessKey) || !StringUtils.hasText(minioSecretKey)) {
            log.error("MinIO客户端创建失败: 配置不完整 - endpoint: {}, accessKey: {}, secretKey: {}", 
                    minioEndpoint, 
                    StringUtils.hasText(minioAccessKey) ? "已配置" : "未配置",
                    StringUtils.hasText(minioSecretKey) ? "已配置" : "未配置");
            throw new IllegalStateException("MinIO配置不完整，无法创建客户端。请检查配置文件中的 minio.endpoint、minio.access-key 和 minio.secret-key 配置项");
        }
        
        try {
            MinioClient client = MinioClient.builder()
                    .endpoint(minioEndpoint)
                    .credentials(minioAccessKey, minioSecretKey)
                    .build();
            log.info("MinIO客户端创建成功 - endpoint: {}", minioEndpoint);
            return client;
        } catch (Exception e) {
            log.error("MinIO客户端创建失败", e);
            throw new IllegalStateException("MinIO客户端创建失败: " + e.getMessage(), e);
        }
    }
}
