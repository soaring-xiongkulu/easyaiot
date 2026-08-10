package com.basiclab.iot.video.config;

import com.basiclab.iot.video.domain.vo.VideoApiResponse;
import com.basiclab.iot.video.exception.VideoBusinessException;
import org.springframework.core.MethodParameter;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.http.converter.HttpMessageConverter;
import org.springframework.http.server.ServerHttpRequest;
import org.springframework.http.server.ServerHttpResponse;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.ResponseStatus;
import org.springframework.web.bind.annotation.RestControllerAdvice;
import org.springframework.web.servlet.mvc.method.annotation.ResponseBodyAdvice;

/**
 * VIDEO 公共 JSON 适配层 — 保证 {@code /video/**} 对外契约与 Python {@code api_response} 一致。
 */
@RestControllerAdvice(basePackages = "com.basiclab.iot.video.controller")
public class VideoApiResponseAdvice implements ResponseBodyAdvice<Object> {

    @Override
    public boolean supports(MethodParameter returnType, Class<? extends HttpMessageConverter<?>> converterType) {
        Class<?> type = returnType.getParameterType();
        if (org.springframework.http.ResponseEntity.class.isAssignableFrom(type)) {
            return false;
        }
        String typeName = type.getName();
        if (typeName.endsWith("SpaceListApiResponse")) {
            return false;
        }
        return returnType.getContainingClass().getPackageName().startsWith("com.basiclab.iot.video.controller");
    }

    @Override
    public Object beforeBodyWrite(
            Object body,
            MethodParameter returnType,
            MediaType selectedContentType,
            Class<? extends HttpMessageConverter<?>> selectedConverterType,
            ServerHttpRequest request,
            ServerHttpResponse response) {
        if (body == null) {
            return VideoApiResponse.success(null);
        }
        if (body instanceof VideoApiResponse) {
            return body;
        }
        String typeName = body.getClass().getName();
        if (typeName.contains("CommonResult")) {
            return VideoApiResponse.error(500, "internal adapter leak: CommonResult must not be returned from VIDEO controllers");
        }
        return VideoApiResponse.success(body);
    }

    @ExceptionHandler(VideoBusinessException.class)
    @ResponseStatus(HttpStatus.OK)
    public VideoApiResponse<Void> handleBusiness(VideoBusinessException ex) {
        return VideoApiResponse.error(ex.getCode(), ex.getMessage());
    }

    @ExceptionHandler(Exception.class)
    @ResponseStatus(HttpStatus.OK)
    public VideoApiResponse<Void> handleException(Exception ex) {
        String msg = ex.getMessage() != null ? ex.getMessage() : ex.getClass().getSimpleName();
        return VideoApiResponse.error(500, msg);
    }
}
