package com.basiclab.iot.device.domain.device.vo;

import com.fasterxml.jackson.annotation.JsonFormat;
import io.swagger.annotations.ApiModel;
import io.swagger.annotations.ApiModelProperty;
import lombok.*;
import lombok.experimental.Accessors;

import java.io.Serializable;
import java.math.BigDecimal;
import java.time.LocalDateTime;

/**
* @Description: java类作用描述
* @author 翱翔的雄库鲁
* @email andywebjava@163.com
* @wechat EasyAIoT2025
* @E-mail: andywebjava@163.com
* @Website: https://gitee.com/soaring-xiongkulu/easyaiot
* @CreateDate: 2024/3/23$ 17:55$
* @UpdateDate: 2024/3/23$ 17:55$
* @UpdateRemark: 修改内容
* @Version: V1.0
*/

/**
 * 设备位置表
 */
@ApiModel(value = "设备位置表")
@Data
@NoArgsConstructor
@AllArgsConstructor
@ToString(callSuper = true)
@Accessors(chain = true)
@Builder
public class DeviceLocation implements Serializable {
    /**
     * 主键
     */
    @ApiModelProperty(value = "主键")
    private Long id;

    /**
     * 设备标识
     */
    @ApiModelProperty(value = "设备标识")
    private String deviceIdentification;

    /**
     * 纬度
     */
    @ApiModelProperty(value = "纬度")
    private BigDecimal latitude;

    /**
     * 经度
     */
    @ApiModelProperty(value = "经度")
    private BigDecimal longitude;

    /**
     * 位置名称
     */
    @ApiModelProperty(value = "位置名称")
    private String fullName;

    /**
     * 省,直辖市编码
     */
    @ApiModelProperty(value = "省,直辖市编码")
    private String provinceCode;

    /**
     * 市编码
     */
    @ApiModelProperty(value = "市编码")
    private String cityCode;

    /**
     * 区县
     */
    @ApiModelProperty(value = "区县")
    private String regionCode;

    /**
     * 创建者
     */
    @ApiModelProperty(value = "创建者")
    private String createBy;

    /**
     * 创建时间
     */
    @ApiModelProperty(value = "创建时间")
    @JsonFormat(pattern = "yyyy-MM-dd HH:mm:ss")
    private LocalDateTime createTime;

    /**
     * 更新者
     */
    @ApiModelProperty(value = "更新者")
    private String updateBy;

    /**
     * 更新时间
     */
    @ApiModelProperty(value = "更新时间")
    @JsonFormat(pattern = "yyyy-MM-dd HH:mm:ss")
    private LocalDateTime updateTime;

    /**
     * 备注
     */
    @ApiModelProperty(value = "备注")
    private String remark;

    private static final long serialVersionUID = 1L;
}