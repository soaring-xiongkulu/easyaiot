package com.basiclab.iot.stream.bean;

import com.baomidou.mybatisplus.annotation.KeySequence;
import com.baomidou.mybatisplus.annotation.TableName;
import io.swagger.v3.oas.annotations.media.Schema;
import lombok.*;

/**
 * @description: 移动位置bean
 * @author: lawrencehj
 * @date: 2021年1月23日
 */
@TableName("wvp_device_mobile_position")
@KeySequence("wvp_device_mobile_position_seq") // 用于 Oracle、PostgreSQL、Kingbase、DB2、H2 数据库的主键自增。如果是 MySQL 等数据库，可不写。
@Data
@ToString(callSuper = true)
@Builder
@NoArgsConstructor
@AllArgsConstructor
@Schema(description = "国标设备/平台")
public class MobilePosition {
    /**
     * 设备Id
     */
    private String deviceId;

    /**
     * 通道Id
     */
    private Integer channelId;

    /**
     * 设备名称
     */
    private String deviceName;

    /**
     * 通知时间
     */
    private String time;

    /**
     * 经度
     */
    private double longitude;

    /**
     * 纬度
     */
    private double latitude;

    /**
     * 海拔高度
     */
    private double altitude;

    /**
     * 速度
     */
    private double speed;

    /**
     * 方向
     */
    private double direction;

    /**
     * 位置信息上报来源（Mobile Position、GPS Alarm）
     */
    private String reportSource;
    /**
     * 创建时间
     */
    private String createTime;
}
