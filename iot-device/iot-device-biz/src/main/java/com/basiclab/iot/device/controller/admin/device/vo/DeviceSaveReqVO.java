package com.basiclab.iot.device.controller.admin.device.vo;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.*;

import javax.validation.constraints.*;
import java.math.BigDecimal;
import java.time.LocalDateTime;

@Schema(description = "管理后台 - 设备新增/修改 Request VO")
@Data
public class DeviceSaveReqVO {

    @Schema(description = "id", requiredMode = Schema.RequiredMode.REQUIRED, example = "10309")
    private Long id;

    @Schema(description = "设备唯一标识", requiredMode = Schema.RequiredMode.REQUIRED, example = "13637")
    @NotEmpty(message = "设备唯一标识不能为空")
    private String did;

    @Schema(description = "设备名称", example = "李四")
    private String name;

    @Schema(description = "设备描述", example = "随便")
    private String description;

    @Schema(description = "设备状态： ENABLE:启用 || DISABLE:禁用", example = "1")
    private String enabledStatus;

    @Schema(description = "连接状态 :    OFFLINE:离线 || ONLINE:在线", example = "1")
    private String connectStatus;

    @Schema(description = "产品唯一标识", requiredMode = Schema.RequiredMode.REQUIRED, example = "31091")
    @NotEmpty(message = "产品唯一标识不能为空")
    private String pid;

    @Schema(description = "创建者")
    private String createBy;

    @Schema(description = "更新者")
    private String updateBy;

    @Schema(description = "备注", example = "你猜")
    private String remark;

    @Schema(description = "设备版本号")
    private String deviceVersion;

    @Schema(description = "设备sn号", requiredMode = Schema.RequiredMode.REQUIRED)
    @NotEmpty(message = "设备sn号不能为空")
    private String deviceSn;

    @Schema(description = "IP地址")
    private String ipAddress;

    @Schema(description = "MAC地址")
    private String macAddress;

    @Schema(description = "激活状态 0:未激活 1:已激活", example = "1")
    private Short activeStatus;

    @Schema(description = "扩展json")
    private String extension;

    @Schema(description = "激活时间")
    private LocalDateTime activatedTime;

    @Schema(description = "最后上线时间")
    private LocalDateTime lastOnlineTime;

    @Schema(description = "子设备关联网关的设备唯一标识", example = "17449")
    private String parentDid;

    @Schema(description = "支持以下两种产品类型	•COMMON：普通产品，需直连设备。	•GATEWAY：网关产品，可挂载子设备。	•SUBSET：子设备。", example = "1")
    private String deviceType;

    @Schema(description = "纬度")
    private BigDecimal latitude;

    @Schema(description = "经度")
    private BigDecimal longitude;

    @Schema(description = "设备所在位置", example = "赵六")
    private String locationName;

    @Schema(description = "省,直辖市编码")
    private String provinceCode;

    @Schema(description = "市编码")
    private String cityCode;

    @Schema(description = "区县")
    private String regionCode;

    @Schema(description = "产品名称", example = "李四")
    private String productName;

    @Schema(description = "是否启用设备影子(0=禁用，1=启用)")
    private Short isShadow;

    @Schema(description = "物模型值")
    private Object thingsModelValue;

    @Schema(description = "产品类型ID", example = "21497")
    private Long productTypeId;

    @Schema(description = "产品类型名称", example = "张三")
    private String productTypeName;

    @Schema(description = "分组ID", example = "3640")
    private Long groupId;

}