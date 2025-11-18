package com.basiclab.iot.dataset.controller;

import com.basiclab.iot.common.domain.CommonResult;
import com.basiclab.iot.dataset.cache.StreamUrlCache;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import static com.basiclab.iot.common.domain.CommonResult.success;

/**
 * StreamController
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@RestController
@RequestMapping("/dataset/streams")
public class StreamController {

    @Autowired
    private StreamUrlCache streamUrlCache;

    @PostMapping("/refresh")
    public CommonResult<String> refreshCache() {
        streamUrlCache.manualRefresh();
        return success("Stream URLs cache refreshed successfully");
    }
}
