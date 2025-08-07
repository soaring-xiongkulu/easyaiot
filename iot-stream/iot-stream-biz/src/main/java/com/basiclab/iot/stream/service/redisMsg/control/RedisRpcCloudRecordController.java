package com.basiclab.iot.stream.service.redisMsg.control;

import com.alibaba.fastjson2.JSONObject;
import com.basiclab.iot.stream.config.UserSetting;
import com.basiclab.iot.stream.config.redis.RedisRpcConfig;
import com.basiclab.iot.stream.config.redis.bean.RedisRpcMessage;
import com.basiclab.iot.stream.config.redis.bean.RedisRpcRequest;
import com.basiclab.iot.stream.config.redis.bean.RedisRpcResponse;
import com.basiclab.iot.stream.service.ICloudRecordService;
import com.basiclab.iot.stream.service.bean.DownloadFileInfo;
import com.basiclab.iot.stream.service.redisMsg.dto.RedisRpcController;
import com.basiclab.iot.stream.service.redisMsg.dto.RedisRpcMapping;
import com.basiclab.iot.stream.service.redisMsg.dto.RpcController;
import com.basiclab.iot.stream.vmanager.bean.ErrorCode;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.data.redis.core.RedisTemplate;
import org.springframework.stereotype.Component;

@Component
@Slf4j
@RedisRpcController("cloudRecord")
public class RedisRpcCloudRecordController extends RpcController {

    @Autowired
    private UserSetting userSetting;

    @Autowired
    private RedisTemplate<Object, Object> redisTemplate;

    @Autowired
    private ICloudRecordService cloudRecordService;


    private void sendResponse(RedisRpcResponse response){
        log.info("[redis-rpc] >> {}", response);
        response.setToId(userSetting.getServerId());
        RedisRpcMessage message = new RedisRpcMessage();
        message.setResponse(response);
        redisTemplate.convertAndSend(RedisRpcConfig.REDIS_REQUEST_CHANNEL_KEY, message);
    }

    /**
     * 播放
     */
    @RedisRpcMapping("play")
    public RedisRpcResponse play(RedisRpcRequest request) {
        int id = Integer.parseInt(request.getParam().toString());
        RedisRpcResponse response = request.getResponse();
        if (id <= 0) {
            response.setStatusCode(ErrorCode.ERROR400.getCode());
            response.setBody("param error");
            return response;
        }
        DownloadFileInfo downloadFileInfo = cloudRecordService.getPlayUrlPath(id);
        if (downloadFileInfo == null) {
            response.setStatusCode(ErrorCode.ERROR100.getCode());
            response.setBody("get play url error");
            return response;
        }
        response.setStatusCode(ErrorCode.SUCCESS.getCode());
        response.setBody(JSONObject.toJSONString(downloadFileInfo));
        return response;
    }

}
