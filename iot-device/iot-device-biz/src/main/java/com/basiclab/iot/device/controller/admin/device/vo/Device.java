package com.basiclab.iot.device.controller.admin.device.vo;

import com.baomidou.mybatisplus.annotation.TableField;
import com.fasterxml.jackson.annotation.JsonFormat;
import lombok.*;
import lombok.experimental.Accessors;

import java.io.Serializable;
import java.time.LocalDateTime;

/**
 * 设备管理
 *
 * @author Basiclab
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
@ToString(callSuper = true)
@Accessors(chain = true)
@Builder
public class Device extends com.basiclab.iot.device.common.BaseEntity implements Serializable {
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

    private String parentIdentification;

    private String deviceType;

    @TableField(exist = false)
    private Boolean isAssociated = false;

    private String remark;

    public static enum deviceTypeEnum {
        /**
         * 网关
         */
        GATEWAY("GATEWAY"),
        /**
         * 普通设备
         */
        COMMON("COMMON"),
        /**
         * 子设备
         */
        SUBSET("SUBSET"),
        /**
         * 视频设备
         */
        VIDEO_COMMON("VIDEO_COMMON");

        private String type;

        deviceTypeEnum(String type) {
            this.type = type;
        }

        public String getType() {
            return type;
        }
    }

    private static final long serialVersionUID = 1L;
}
