package com.basiclab.iot.dataset.enums.dataset;

import lombok.AllArgsConstructor;
import lombok.Getter;

/**
 * DatasetFrameType
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Getter
@AllArgsConstructor
public enum DatasetFrameType {

    /**
     * 实时流帧捕获
     */
    LIVE_VIDEO_FRAME(0, "LIVE_VIDEO_FRAME"),

    /**
     * GB28181流帧捕获
     */
    GB28181_VIDEO_FRAME(1, "GB28181_VIDEO_FRAME");

    private Integer key;
    private String value;

}
