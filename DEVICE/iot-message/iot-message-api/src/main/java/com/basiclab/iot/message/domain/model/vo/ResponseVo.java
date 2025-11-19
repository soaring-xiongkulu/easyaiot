package com.basiclab.iot.message.domain.model.vo;

import lombok.Data;

/**
 * response相应实体
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 * @since 2023-07-19
 **/
@Data
public class ResponseVo<T> {
    private T data;
    private int status=200;
    private String message;

    public ResponseVo(T data) {
        this.data = data;
    }
    public ResponseVo() {
       super();
    }

    public ResponseVo(int status, String message) {
        this.status = status;
        this.message = message;
    }
}
