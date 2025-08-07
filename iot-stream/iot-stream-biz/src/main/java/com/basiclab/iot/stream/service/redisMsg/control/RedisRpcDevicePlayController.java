package com.basiclab.iot.stream.service.redisMsg.control;

import com.alibaba.fastjson2.JSON;
import com.alibaba.fastjson2.JSONObject;
import com.basiclab.iot.stream.config.UserSetting;
import com.basiclab.iot.stream.config.redis.RedisRpcConfig;
import com.basiclab.iot.stream.config.redis.bean.RedisRpcMessage;
import com.basiclab.iot.stream.config.redis.bean.RedisRpcRequest;
import com.basiclab.iot.stream.config.redis.bean.RedisRpcResponse;
import com.basiclab.iot.stream.bean.Device;
import com.basiclab.iot.stream.service.IDeviceService;
import com.basiclab.iot.stream.service.IPlayService;
import com.basiclab.iot.stream.service.redisMsg.dto.RedisRpcController;
import com.basiclab.iot.stream.service.redisMsg.dto.RedisRpcMapping;
import com.basiclab.iot.stream.service.redisMsg.dto.RpcController;
import com.basiclab.iot.stream.vmanager.bean.AudioBroadcastResult;
import com.basiclab.iot.stream.vmanager.bean.ErrorCode;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.data.redis.core.RedisTemplate;
import org.springframework.stereotype.Component;

@Component
@Slf4j
@RedisRpcController("devicePlay")
public class RedisRpcDevicePlayController extends RpcController {

    @Autowired
    private UserSetting userSetting;

    @Autowired
    private RedisTemplate<Object, Object> redisTemplate;

    @Autowired
    private IDeviceService deviceService;

    @Autowired
    private IPlayService playService;



    private void sendResponse(RedisRpcResponse response){
        log.info("[redis-rpc] >> {}", response);
        response.setToId(userSetting.getServerId());
        RedisRpcMessage message = new RedisRpcMessage();
        message.setResponse(response);
        redisTemplate.convertAndSend(RedisRpcConfig.REDIS_REQUEST_CHANNEL_KEY, message);
    }

    /**
     * 获取通道同步状态
     */
    @RedisRpcMapping("audioBroadcast")
    public RedisRpcResponse audioBroadcast(RedisRpcRequest request) {
        JSONObject paramJson = JSON.parseObject(request.getParam().toString());
        String deviceId = paramJson.getString("deviceId");
        String channelDeviceId = paramJson.getString("channelDeviceId");
        Boolean broadcastMode = paramJson.getBoolean("broadcastMode");

        Device device = deviceService.getDeviceByDeviceId(deviceId);

        RedisRpcResponse response = request.getResponse();
        if (device == null || !userSetting.getServerId().equals(device.getServerId())) {
            response.setStatusCode(ErrorCode.ERROR400.getCode());
            response.setBody("param error");
            return response;
        }
        AudioBroadcastResult audioBroadcastResult = playService.audioBroadcast(deviceId, channelDeviceId, broadcastMode);
        response.setStatusCode(ErrorCode.SUCCESS.getCode());
        response.setBody(JSONObject.toJSONString(audioBroadcastResult));
        return response;
    }

}
