package com.basiclab.iot.sink.config;

import lombok.Data;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.stereotype.Component;

/**
 * NFS 共享媒体挂载（唯一存储方式；未指定 NFS 服务端时使用本机 export 路径）。
 */
@Data
@Component
@ConfigurationProperties(prefix = "basiclab.media")
public class NfsMediaProperties {

    /** 媒体挂载根，如 /mnt/easyaiot-media */
    private String mountRoot = "/mnt/easyaiot-media";

    /** SRS 容器内数据根，Hook 路径 /data/... 映射到 mountRoot */
    private String containerDataRoot = "/data";

    /** 仅允许读写 mountRoot 下路径 */
    private boolean nfsOnly = true;

    /** DVR 上传成功后删除 NFS 上的本地 flv（与 VIDEO REMOVE_LOCAL_AFTER_MINIO 一致） */
    private boolean removeLocalAfterUpload = true;
}
