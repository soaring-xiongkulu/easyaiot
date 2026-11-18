package com.basiclab.iot.device.domain.device.vo;

import io.swagger.annotations.ApiModelProperty;
import lombok.Data;

/**
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Data
public class TDDeviceDataResp {
    /**
     * 时间
     */
    @ApiModelProperty("时间")
    private long ts;
    /**
     * 标识符
     */
    @ApiModelProperty("标识符")
    private String propertyCode;
    /**
     * 属性名称
     */
    @ApiModelProperty("属性名称")
    private String propertyName;

    /**
     * 设备点位自定义名称。为空时前端回退到物模型属性名称。
     */
    @ApiModelProperty("点位名称")
    private String pointName;

    /**
     * 点位数值展示的小数位数；为空表示使用默认的浮点误差归一化展示。
     */
    @ApiModelProperty("显示小数位数")
    private Integer decimalPlaces;
    /**
     * 数据类型
      */
    @ApiModelProperty("数据类型")
    private String datatype;
    /**
     * 数据
     */
    @ApiModelProperty("数据")
    private String dataValue;

    /**
     * 工业协议采集时保存的原始响应数据段。
     */
    @ApiModelProperty("原始响应数据")
    private String rawData;

    /**
     * 指示单位。支持长度不超过50。
     取值根据参数确定，如：
     •温度单位：“C”或“K”
     •百分比单位：“%”
     •压强单位：“Pa”或“kPa”
     */
    @ApiModelProperty(value="指示单位。支持长度不超过50。,取值根据参数确定，如：,•温度单位：“C”或“K”,•百分比单位：“%”,•压强单位：“Pa”或“kPa”,")
    private String unit;

}
