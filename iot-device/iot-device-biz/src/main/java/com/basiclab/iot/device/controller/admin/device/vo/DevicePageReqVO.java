package com.basiclab.iot.device.controller.admin.device.vo;

import lombok.*;
import io.swagger.v3.oas.annotations.media.Schema;
import com.basiclab.iot.common.domain.PageParam;
import java.math.BigDecimal;
import org.springframework.format.annotation.DateTimeFormat;
import java.time.LocalDateTime;

import static com.basiclab.iot.common.utils.date.DateUtils.FORMAT_YEAR_MONTH_DAY_HOUR_MINUTE_SECOND;

@Schema(description = "管理后台 - 设备分页 Request VO")
@Data
@EqualsAndHashCode(callSuper = true)
@ToString(callSuper = true)
public class DevicePageReqVO extends PageParam {

    @Schema(description = "设备唯一标识", example = "13637")
    private String did;

    @Schema(description = "设备名称", example = "李四")
    private String name;

    @Schema(description = "设备描述", example = "随便")
    private String description;

    @Schema(description = "设备状态： ENABLE:启用 || DISABLE:禁用", example = "1")
    private String enabledStatus;

    @Schema(description = "连接状态 :    OFFLINE:离线 || ONLINE:在线", example = "1")
    private String connectStatus;

    @Schema(description = "产品唯一标识", example = "31091")
    private String pid;

    @Schema(description = "创建者")
    private String createBy;

    @Schema(description = "创建时间")
    @DateTimeFormat(pattern = FORMAT_YEAR_MONTH_DAY_HOUR_MINUTE_SECOND)
    private LocalDateTime[] createTime;

    @Schema(description = "更新者")
    private String updateBy;

    @Schema(description = "备注", example = "你猜")
    private String remark;

    @Schema(description = "设备版本号")
    private String deviceVersion;

    @Schema(description = "设备sn号")
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
    @DateTimeFormat(pattern = FORMAT_YEAR_MONTH_DAY_HOUR_MINUTE_SECOND)
    private LocalDateTime[] activatedTime;

    @Schema(description = "最后上线时间")
    @DateTimeFormat(pattern = FORMAT_YEAR_MONTH_DAY_HOUR_MINUTE_SECOND)
    private LocalDateTime[] lastOnlineTime;

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