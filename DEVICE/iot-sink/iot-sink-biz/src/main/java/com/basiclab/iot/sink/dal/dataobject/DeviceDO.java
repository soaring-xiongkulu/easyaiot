package com.basiclab.iot.sink.dal.dataobject;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.*;

import java.time.LocalDateTime;

/**
 * DeviceDO
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */

@TableName("device")
@Data
@ToString(callSuper = true)
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class DeviceDO {

    /**
     * 主键ID
     */
    @TableId(type = IdType.AUTO)
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
     * 用户名
     */
    private String userName;

    /**
     * 密码
     */
    private String password;

    /**
     * 产品标识
     */
    private String productIdentification;

    /**
     * 设备状态：ENABLE:启用 || DISABLE:禁用
     */
    private String deviceStatus;

    /**
     * 连接状态：OFFLINE:离线 || ONLINE:在线
     */
    private String connectStatus;

    /**
     * 协议类型
     */
    private String protocolType;

    /**
     * 租户编号
     */
    private Long tenantId;

    /**
     * 创建者
     */
    private String createBy;

    /**
     * 创建时间
     */
    private LocalDateTime createTime;

    /**
     * 更新者
     */
    private String updateBy;

    /**
     * 更新时间
     */
    private LocalDateTime updateTime;
}

