package com.basiclab.iot.device.constant;

import lombok.Getter;
/**
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 * @desc
 * @created 2025-06-03
 */
public enum OpsFileUploadStatus {

    SUCCESS(0, "上传成功"),
    START(1, "未开始"),
    UPLOADING(2, "上传中"),
    ERROR(3, "上传失败"),
    ;
    @Getter
    private Integer code;
    @Getter
    private String desc;

    OpsFileUploadStatus(int code, String desc){
        this.code = code;
        this.desc = desc;
    }

    public static OpsFileUploadStatus get(int code) {
        OpsFileUploadStatus[] es = OpsFileUploadStatus.values();
        for (OpsFileUploadStatus e : es) {
            if (code == e.getCode()) {
                return e;
            }
        }
        return OpsFileUploadStatus.SUCCESS;
    }
}
