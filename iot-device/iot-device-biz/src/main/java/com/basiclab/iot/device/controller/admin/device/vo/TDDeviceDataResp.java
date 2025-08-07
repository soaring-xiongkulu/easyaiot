package com.basiclab.iot.device.controller.admin.device.vo;

import lombok.Data;

/**
 * @author Basiclab
 */
@Data
public class TDDeviceDataResp {
    /**
     * 时间
     */
    private long ts;
    /**
     * 标识符
     */
    private String propertyCode;
    /**
     * 属性名称
     */
    private String propertyName;
    /**
     * 数据类型
     */
    private String datatype;
    /**
     * 数据
     */
    private String dataValue;

    /**
     * 指示单位。支持长度不超过50。
     * 取值根据参数确定，如：
     * •温度单位：“C”或“K”
     * •百分比单位：“%”
     * •压强单位：“Pa”或“kPa”
     */
    private String unit;

}
