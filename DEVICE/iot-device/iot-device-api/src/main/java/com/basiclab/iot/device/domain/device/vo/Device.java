package com.basiclab.iot.device.domain.device.vo;

import com.baomidou.mybatisplus.annotation.TableField;
import com.fasterxml.jackson.annotation.JsonFormat;
import com.basiclab.iot.common.annotation.Excel;
import com.basiclab.iot.common.domain.BaseEntity;
import io.swagger.annotations.ApiModel;
import io.swagger.annotations.ApiModelProperty;
import lombok.*;
import lombok.experimental.Accessors;

import java.io.Serializable;
import java.time.LocalDateTime;

/**
 * 设备管理
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@EqualsAndHashCode(callSuper = true)
@ApiModel(value = "设备管理")
@Data
@NoArgsConstructor
@AllArgsConstructor
@ToString(callSuper = true)
@Accessors(chain = true)
@Builder
public class Device extends BaseEntity implements Serializable{
    /**
     * id
     */
    @Excel(name = "id", cellType = Excel.ColumnType.NUMERIC, prompt = "id")
    @ApiModelProperty(value = "id", hidden = true)
    private Long id;

    /**
     * 客户端标识
     */
    @Excel(name = "客户端标识")
    @ApiModelProperty(value = "客户端标识")
    private String clientId;

    /**
     * 应用ID
     */
    @Excel(name = "应用ID")
    @ApiModelProperty(value = "应用ID")
    private String appId;

    /**
     * 设备标识
     */
    @Excel(name = "设备标识")
    @ApiModelProperty(value = "设备标识")
    private String deviceIdentification;

    /**
     * 设备名称
     */
    @Excel(name = "设备名称")
    @ApiModelProperty(value = "设备名称")
    private String deviceName;

    /**
     * 设备描述
     */
    @Excel(name = "设备描述")
    @ApiModelProperty(value = "设备描述")
    private String deviceDescription;

    /**
     * 设备状态： 启用 || 禁用
     */
    @Excel(name = "设备状态")
    @ApiModelProperty(value = "设备状态： 启用 || 禁用")
    private String deviceStatus;

    /**
     * 连接状态 : 在线：ONLINE || 离线：OFFLINE || 未连接：INIT
     */
    @Excel(name = "连接状态")
    @ApiModelProperty(value = "连接状态 : 在线：ONLINE || 离线：OFFLINE || 未连接：INIT,")
    private String connectStatus;

    /**
     * 是否遗言
     */
    @Excel(name = "是否遗言")
    @ApiModelProperty(value = "是否遗言")
    private String isWill;

    /**
     * 产品标识
     */
    @Excel(name = "产品标识")
    @ApiModelProperty(value = "产品标识")
    private String productIdentification;

    /**
     * 设备版本
     */
    @Excel(name = "设备版本")
    @ApiModelProperty(value = "设备版本")
    private String deviceVersion;

    /**
     * 设备sn号
     */
    @Excel(name = "设备sn号")
    @ApiModelProperty(value = "设备sn号")
    private String deviceSn;

    /**
     * ip地址
     */
    @Excel(name = "ip地址")
    @ApiModelProperty(value = "ip地址")
    private String ipAddress;

    /**
     * 激活时间
     */
    @Excel(name = "激活时间")
    @ApiModelProperty(value = "激活时间")
    @JsonFormat(pattern = "yyyy-MM-dd HH:mm:ss")
    private LocalDateTime activatedTime;

    /**
     * 最后上线时间
     */
    @Excel(name = "最后上线时间")
    @ApiModelProperty(value = "最后上线时间")
    @JsonFormat(pattern = "yyyy-MM-dd HH:mm:ss")
    private LocalDateTime lastOnlineTime;

    /**
     * mac地址
     */
    @Excel(name = "mac地址")
    @ApiModelProperty(value = "mac地址")
    private String macAddress;

    /**
     * 激活状态
     */
    @Excel(name = "激活状态")
    @ApiModelProperty(value = "激活状态")
    private Integer activeStatus;

    /**
     * 扩展Json
     */
    @Excel(name = "扩展Json")
    @ApiModelProperty(value = "扩展Json")
    private String extension;

    @ApiModelProperty(value = "所属网关设备标识")
    private String parentIdentification;

    @ApiModelProperty(value = "支持以下两种产品类型•COMMON：普通产品，需直连设备。,•GATEWAY：网关产品，可挂载子设备。,•SUBSET：子设备。")
    private String deviceType;

    @ApiModelProperty(value = "是否已关联网关")
    @TableField(exist = false)
    private Boolean isAssociated = false;

    @ApiModelProperty(value = "备注")
    private String remark;

    public static enum deviceTypeEnum{
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
        VIDEO_COMMON("VIDEO_COMMON")
        ;

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
