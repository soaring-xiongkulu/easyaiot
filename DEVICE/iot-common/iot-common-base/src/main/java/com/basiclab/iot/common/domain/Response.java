package com.basiclab.iot.common.domain;

import com.basiclab.iot.common.exception.BaseException;
import com.basiclab.iot.common.exception.ErrorCode;
import com.basiclab.iot.common.exception.GlobalErrorStatus;
import com.basiclab.iot.common.exception.Status;
import com.fasterxml.jackson.annotation.JsonInclude;
import io.swagger.annotations.ApiModel;
import io.swagger.annotations.ApiModelProperty;
import lombok.Data;
import lombok.experimental.Accessors;

import java.text.MessageFormat;

/**
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 * @desc
 * @created 2025-05-27
 */
@Data
@Accessors(chain = true)
@JsonInclude(JsonInclude.Include.NON_NULL)
@ApiModel(value = "接口响应数据", description = "用于返回接口响应的内容")
public class Response<T> {

    @ApiModelProperty(value = "请求响应状态码，0-成功，-1-未知，其他自定义", example = "0")
    private Integer code = 0;

    @ApiModelProperty(value = "请求响应消息", example = "")
    private String message = "";

    @ApiModelProperty(value = "请求响应详细消息", example = "")
    private Object detailMessage;

    @ApiModelProperty(value = "请求响应数据")
    private T data;

    public Response() {
        this(null);
    }

    public Response(T data) {
        this.data = data;
    }

    public static Response success() {
        return new Response();
    }

    public static <T> Response success(T data) {
        return new Response(data);
    }

    public static Response error() {
        return error("");
    }

    public static Response error(String message) {
        Response response = new Response();
        response.setCode(-1);
        response.setMessage(message);
        return response;
    }

    public static Response error(int code, String message) {
        Response response = new Response();
        response.setCode(code);
        response.setMessage(message);
        return response;
    }

    public static Response error(BaseException ex ) {
        Response response = new Response();
        response.setCode(Integer.parseInt(ex.getCode()));
        response.setMessage(ex.getMessage());
        return response;
    }

    public static Response error(ErrorCode status) {
        Response response = new Response();
        response.setCode(status.getCode());
        response.setMessage(status.getMsg());
        return response;
    }

    public static Response error(ErrorCode status, Object... args) {
        Response response = new Response();
        response.setCode(status.getCode());
        response.setMessage(format(status.getMsg(), args));
        return response;
    }

    private static String format(String pattern, Object... arguments) {
        return MessageFormat.format(pattern, arguments);
    }
}
