package com.basiclab.iot.device.domain.app.vo;

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
 * 应用密钥 VO
 * <p>
 * 用于管理设备的 appId、appKey、appSecret
 *
 * @author 翱翔的雄库鲁
 */
@EqualsAndHashCode(callSuper = true)
@ApiModel(value = "应用密钥")
@Data
@NoArgsConstructor
@AllArgsConstructor
@ToString(callSuper = true)
@Accessors(chain = true)
@Builder
public class App extends BaseEntity implements Serializable {

    /**
     * 主键ID
     */
    @ApiModelProperty(value = "主键ID")
    private Long id;

    /**
     * 应用ID（AppID）：应用的唯一标识
     */
    @ApiModelProperty(value = "应用ID（AppID）")
    private String appId;

    /**
     * 应用密钥（AppKey）：公匙，相当于账号
     */
    @ApiModelProperty(value = "应用密钥（AppKey）")
    private String appKey;

    /**
     * 应用密钥（AppSecret）：私匙，相当于密码
     */
    @ApiModelProperty(value = "应用密钥（AppSecret）")
    private String appSecret;

    /**
     * 应用名称
     */
    @ApiModelProperty(value = "应用名称")
    private String appName;

    /**
     * 应用描述
     */
    @ApiModelProperty(value = "应用描述")
    private String appDesc;

    /**
     * 状态：ENABLE-启用，DISABLE-禁用
     */
    @ApiModelProperty(value = "状态：ENABLE-启用，DISABLE-禁用")
    private String status;

    /**
     * 权限类型：READ_ONLY-只读，READ_WRITE-读写
     */
    @ApiModelProperty(value = "权限类型：READ_ONLY-只读，READ_WRITE-读写")
    private String permissionType;

    /**
     * 过期时间
     */
    @ApiModelProperty(value = "过期时间")
    @JsonFormat(pattern = "yyyy-MM-dd HH:mm:ss")
    private LocalDateTime expireTime;

    /**
     * 租户编号
     */
    @ApiModelProperty(value = "租户编号")
    private Long tenantId;

    /**
     * 备注
     */
    @ApiModelProperty(value = "备注")
    private String remark;
}

