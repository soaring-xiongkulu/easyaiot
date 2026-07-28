package com.basiclab.iot.transform.runtime.web;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * 统一 API 响应。
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
public class R<T> {

    private int code;
    private String msg;
    private T data;

    public static <T> R<T> ok(T data) {
        return new R<>(0, "success", data);
    }

    public static <T> R<T> fail(String msg) {
        return new R<>(-1, msg, null);
    }
}
