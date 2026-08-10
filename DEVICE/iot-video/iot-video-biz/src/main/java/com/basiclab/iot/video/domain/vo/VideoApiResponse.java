package com.basiclab.iot.video.domain.vo;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * VIDEO 对外 JSON 外壳，对齐 Python {@code api_response}：{@code {code, msg, message, data}}。
 * <p>业务成功 {@code code=0}，HTTP 状态码仍为 200。</p>
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
public class VideoApiResponse<T> {

    private int code;
    private String msg;
    private String message;
    private T data;
    private Integer total;

    public static <T> VideoApiResponse<T> success(T data) {
        return success("success", data);
    }

    public static <T> VideoApiResponse<T> success(String msg, T data) {
        VideoApiResponse<T> response = new VideoApiResponse<>();
        response.setCode(0);
        response.setMsg(msg);
        response.setMessage(msg);
        response.setData(data);
        return response;
    }

    public static <T> VideoApiResponse<T> error(int code, String msg) {
        VideoApiResponse<T> response = new VideoApiResponse<>();
        response.setCode(code);
        response.setMsg(msg);
        response.setMessage(msg);
        response.setData(null);
        return response;
    }
}
