package com.basiclab.iot.stream.bean;

import com.basiclab.iot.stream.utils.MessageElement;
import lombok.Data;

/**
 * 设备信息查询响应
 *
 * @author Y.G
 * @version 1.0
 * @date 2022/6/28 14:55
 */
@Data
public class DragZoomRequest {
    /**
     * 序列号
     */
    @MessageElement("SN")
    private String sn;

    @MessageElement("DeviceID")
    private String deviceId;

    @MessageElement(value = "DragZoomIn")
    private DragZoomParam dragZoomIn;

    @MessageElement(value = "DragZoomOut")
    private DragZoomParam dragZoomOut;

}
