package com.basiclab.iot.device.domain.device.oo;

import lombok.Data;

/**
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 * @desc
 * @created 2025-06-03
 */
@Data
public class OssUploadResultOo {
    private String ossUrl;
    private String ossKey;
    private String eTag;
    private String fileType;
    /**
     * This uuid is null when the specified OssUploadOo.ossKey is uploaded.
     */
    private String uuid;
}