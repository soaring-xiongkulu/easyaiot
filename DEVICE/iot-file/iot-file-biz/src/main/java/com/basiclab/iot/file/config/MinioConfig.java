package com.basiclab.iot.file.config;

import com.basiclab.iot.file.service.ISysFileService;
import com.basiclab.iot.file.service.MinioSysFileServiceImpl;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import io.minio.MinioClient;
import org.springframework.context.annotation.Primary;
import org.springframework.util.StringUtils;

import javax.annotation.PostConstruct;

/**
 * Minio 配置信息
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Configuration
@ConfigurationProperties(prefix = "minio")
public class MinioConfig
{
    private static final Logger log = LoggerFactory.getLogger(MinioConfig.class);

    /**
     * 服务地址
     */
    private String url;

    /**
     * 服务地址
     */
    private String downloadUrl;

    /**
     * 用户名
     */
    private String accessKey;

    /**
     * 密码
     */
    private String secretKey;

    /**
     * 存储桶名称
     */
    private String bucketName;

    public String getUrl()
    {
        return url;
    }

    public void setUrl(String url)
    {
        this.url = url;
    }

    public String getDownloadUrl() {
        return downloadUrl;
    }

    public void setDownloadUrl(String downloadUrl) {
        this.downloadUrl = downloadUrl;
    }

    public String getAccessKey()
    {
        return accessKey;
    }

    public void setAccessKey(String accessKey)
    {
        this.accessKey = accessKey;
    }

    public String getSecretKey()
    {
        return secretKey;
    }

    public void setSecretKey(String secretKey)
    {
        this.secretKey = secretKey;
    }

    public String getBucketName()
    {
        return bucketName;
    }

    public void setBucketName(String bucketName)
    {
        this.bucketName = bucketName;
    }

    /**
     * 验证配置是否完整
     */
    @PostConstruct
    public void validateConfig() {
        if (!StringUtils.hasText(url)) {
            log.error("MinIO配置错误: url 未配置");
            throw new IllegalStateException("MinIO配置错误: url 未配置，请在配置文件中设置 minio.url");
        }
        if (!StringUtils.hasText(accessKey)) {
            log.error("MinIO配置错误: accessKey 未配置");
            throw new IllegalStateException("MinIO配置错误: accessKey 未配置，请在配置文件中设置 minio.accessKey");
        }
        if (!StringUtils.hasText(secretKey)) {
            log.error("MinIO配置错误: secretKey 未配置");
            throw new IllegalStateException("MinIO配置错误: secretKey 未配置，请在配置文件中设置 minio.secretKey");
        }
        if (!StringUtils.hasText(bucketName)) {
            log.warn("MinIO配置警告: bucketName 未配置，可能影响文件上传功能");
        }
        
        // 记录配置信息（隐藏敏感信息）
        log.info("MinIO配置加载成功 - url: {}, downloadUrl: {}, accessKey: {}, bucketName: {}", 
                url, downloadUrl, 
                StringUtils.hasText(accessKey) ? maskString(accessKey) : "未配置",
                bucketName);
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
    public MinioClient getMinioClient()
    {
        if (!StringUtils.hasText(url) || !StringUtils.hasText(accessKey) || !StringUtils.hasText(secretKey)) {
            log.error("MinIO客户端创建失败: 配置不完整 - url: {}, accessKey: {}, secretKey: {}", 
                    url, 
                    StringUtils.hasText(accessKey) ? "已配置" : "未配置",
                    StringUtils.hasText(secretKey) ? "已配置" : "未配置");
            throw new IllegalStateException("MinIO配置不完整，无法创建客户端。请检查配置文件中的 minio.url、minio.accessKey 和 minio.secretKey 配置项");
        }
        
        try {
            MinioClient client = MinioClient.builder()
                    .endpoint(url)
                    .credentials(accessKey, secretKey)
                    .build();
            log.info("MinIO客户端创建成功 - endpoint: {}", url);
            return client;
        } catch (Exception e) {
            log.error("MinIO客户端创建失败", e);
            throw new IllegalStateException("MinIO客户端创建失败: " + e.getMessage(), e);
        }
    }

    @Bean
    @Primary
    public ISysFileService getSysFileService()
    {
        return new MinioSysFileServiceImpl();
    }
}
