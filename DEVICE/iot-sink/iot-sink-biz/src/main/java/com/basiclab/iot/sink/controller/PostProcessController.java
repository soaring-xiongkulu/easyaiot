package com.basiclab.iot.sink.controller;

import com.basiclab.iot.common.domain.CommonResult;
import com.basiclab.iot.sink.domain.model.PostProcessRequestMessage;
import com.basiclab.iot.sink.service.PostProcessService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

/**
 * 算法后处理入队 API（VIDEO 算法检测侧 HTTP 投递，由 iot-sink 对接 Kafka）
 */
@Slf4j
@Tag(name = "算法后处理")
@RestController
@RequestMapping("/post-process")
@RequiredArgsConstructor
public class PostProcessController {

    private final PostProcessService postProcessService;

    @PostMapping("/enqueue")
    @Operation(summary = "后处理请求入队（写入 Kafka request 主题）")
    public CommonResult<Boolean> enqueue(@RequestBody PostProcessRequestMessage message) {
        try {
            postProcessService.enqueue(message);
            return CommonResult.success(true);
        } catch (IllegalArgumentException | IllegalStateException ex) {
            log.warn("后处理入队失败: {}", ex.getMessage());
            return CommonResult.error(500, ex.getMessage());
        }
    }
}
