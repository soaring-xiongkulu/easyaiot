package com.basiclab.iot.device.domain.device.vo;

import lombok.Data;

import java.io.Serializable;

/**
 * (DeviceBatchDetail)实体类
 *
 * @author makejava
 * @since 2025-06-18 14:38:13
 */
@Data
public class DeviceBatchDetail implements Serializable {
    private static final long serialVersionUID = -59336604825338952L;
    /**
     * 主键id
     */
    private Integer id;
    /**
     * 设备批次id
     */
    private String batchNumber;
    /**
     * 设备名称
     */
    private String deviceName;
    /**
     * 设备sn码
     */
    private String deviceSn;
    /**
     * 设备标识
     */
    private String deviceIdentification;
    /**
     * 创建状态
     */
    private Integer createStatus;
    /**
     * 失败原因
     */
    private String failureCase;

    public static enum CreateStatusEnum{
        /**
         * 成功
         */
        SUCCESS(1),
        /**
         * 失败
         */
        FAILURE(2);
        private final Integer status;

        CreateStatusEnum(Integer status) {
            this.status = status;
        }

        public Integer getStatus() {
            return status;
        }
    }
}

