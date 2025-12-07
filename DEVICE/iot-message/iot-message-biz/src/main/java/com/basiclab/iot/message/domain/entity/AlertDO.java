package com.basiclab.iot.message.domain.entity;

import lombok.Data;

import java.time.LocalDateTime;

/**
 * Alert实体类（对应VIDEO数据库中的alert表）
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Data
public class AlertDO {

    /**
     * 告警ID（主键，自增）
     */
    private Integer id;

    /**
     * 对象类型
     */
    private String object;

    /**
     * 事件类型
     */
    private String event;

    /**
     * 区域
     */
    private String region;

    /**
     * 详细信息（可以是JSON字符串）
     */
    private String information;

    /**
     * 告警时间
     */
    private LocalDateTime time;

    /**
     * 设备ID
     */
    private String deviceId;

    /**
     * 设备名称
     */
    private String deviceName;

    /**
     * 图片路径（MinIO路径或本地路径）
     */
    private String imagePath;

    /**
     * 录像路径
     */
    private String recordPath;
}

