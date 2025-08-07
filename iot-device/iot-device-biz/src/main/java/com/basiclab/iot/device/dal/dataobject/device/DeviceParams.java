package com.basiclab.iot.device.dal.dataobject.device;

import com.fasterxml.jackson.annotation.JsonFormat;
import lombok.Data;

import java.io.Serializable;
import java.time.LocalDateTime;

@Data
public class DeviceParams implements Serializable {
    private static final long serialVersionUID = 1L;

    /**
     * id
     */
    private Long id;

    /**
     * 客户端标识
     */
    private String clientId;

    /**
     * 应用ID
     */
    private String appId;

    /**
     * 设备标识
     */
    private String deviceIdentification;

    /**
     * 设备名称
     */
    private String deviceName;

    /**
     * 设备描述
     */
    private String deviceDescription;

    /**
     * 设备状态： 启用 || 禁用
     */
    private String deviceStatus;

    /**
     * 连接状态 : 在线：ONLINE || 离线：OFFLINE || 未连接：INIT
     */
    private String connectStatus;

    /**
     * 是否遗言
     */
    private String isWill;

    /**
     * 产品标识
     */
    private String productIdentification;

    /**
     * 设备版本
     */
    private String deviceVersion;

    /**
     * 设备sn号
     */
    private String deviceSn;

    /**
     * ip地址
     */
    private String ipAddress;

    /**
     * 激活时间
     */
    @JsonFormat(pattern = "yyyy-MM-dd HH:mm:ss")
    private LocalDateTime activatedTime;

    /**
     * 最后上线时间
     */
    @JsonFormat(pattern = "yyyy-MM-dd HH:mm:ss")
    private LocalDateTime lastOnlineTime;

    /**
     * mac地址
     */
    private String macAddress;

    /**
     * 激活状态
     */
    private Integer activeStatus;

    /**
     * 扩展Json
     */
    private String extension;

}
