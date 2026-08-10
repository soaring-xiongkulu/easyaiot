package com.basiclab.iot.video.config;

import com.basiclab.iot.video.domain.vo.VideoApiResponse;
import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.ResponseStatus;
import org.springframework.web.bind.annotation.RestControllerAdvice;

/**
 * VIDEO 公共 JSON 适配层。
 * <p>
 * 目的：保证 {@code /video/**} 对外契约与 Python Flask {@code api_response} 一致
 * （{@code {code, msg, message, data}}），避免 DEVICE 默认 {@code CommonResult} 外壳
 * （含 {@code list}/{@code total} 等字段）泄漏到 VIDEO 公共端点。
 * </p>
 * <p>VIDEO controller 应显式返回 {@link VideoApiResponse}，不要返回 {@code CommonResult}。</p>
 */
@RestControllerAdvice(basePackages = "com.basiclab.iot.video.controller")
public class VideoApiResponseAdvice {

    @ExceptionHandler(Exception.class)
    @ResponseStatus(HttpStatus.OK)
    public VideoApiResponse<Void> handleException(Exception ex) {
        return VideoApiResponse.error(500, ex.getMessage() != null ? ex.getMessage() : "internal error");
    }
}
