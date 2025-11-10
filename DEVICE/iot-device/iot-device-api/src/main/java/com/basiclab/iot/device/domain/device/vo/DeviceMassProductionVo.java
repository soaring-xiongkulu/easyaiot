package com.basiclab.iot.device.domain.device.vo;

import com.alibaba.excel.annotation.ExcelProperty;
import com.alibaba.excel.annotation.write.style.ColumnWidth;
import io.swagger.annotations.ApiModel;
import lombok.Getter;
import lombok.Setter;

import java.io.Serializable;

/**
 * 设备管理
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@ApiModel(value = "设备量产信息")
@Getter
@Setter
public class DeviceMassProductionVo implements Serializable{

    /**
     * 设备标识
     */
    @ExcelProperty(value = "设备标识")
    @ColumnWidth(value = 50)
    private String deviceIdentification;

    /**
     * 设备sn号
     */
    @ExcelProperty(value = "设备sn号")
    @ColumnWidth(value = 50)
    private String deviceSn;


    private static final long serialVersionUID = 1123123L;
}
