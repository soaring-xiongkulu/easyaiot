package com.basiclab.iot.stream.service.redisMsg.control;

import com.alibaba.fastjson2.JSONObject;
import com.basiclab.iot.stream.common.StreamInfo;
import com.basiclab.iot.stream.config.UserSetting;
import com.basiclab.iot.stream.config.redis.RedisRpcConfig;
import com.basiclab.iot.stream.config.redis.bean.RedisRpcMessage;
import com.basiclab.iot.stream.config.redis.bean.RedisRpcRequest;
import com.basiclab.iot.stream.config.redis.bean.RedisRpcResponse;
import com.basiclab.iot.stream.service.redisMsg.dto.RedisRpcController;
import com.basiclab.iot.stream.service.redisMsg.dto.RedisRpcMapping;
import com.basiclab.iot.stream.service.redisMsg.dto.RpcController;
import com.basiclab.iot.stream.streamProxy.bean.StreamProxy;
import com.basiclab.iot.stream.streamProxy.service.IStreamProxyPlayService;
import com.basiclab.iot.stream.streamProxy.service.IStreamProxyService;
import com.basiclab.iot.stream.vmanager.bean.ErrorCode;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.data.redis.core.RedisTemplate;
import org.springframework.stereotype.Component;

@Component
@Slf4j
@RedisRpcController("streamProxy")
public class RedisRpcStreamProxyController extends RpcController {

    @Autowired
    private UserSetting userSetting;

    @Autowired
    private RedisTemplate<Object, Object> redisTemplate;

    @Autowired
    private IStreamProxyPlayService streamProxyPlayService;

    @Autowired
    private IStreamProxyService streamProxyService;


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
        StreamProxy streamProxy = streamProxyService.getStreamProxy(id);
        if (streamProxy == null) {
            response.setStatusCode(ErrorCode.ERROR400.getCode());
            response.setBody("param error");
            return response;
        }
        StreamInfo streamInfo = streamProxyPlayService.startProxy(streamProxy);
        response.setStatusCode(ErrorCode.SUCCESS.getCode());
        response.setBody(JSONObject.toJSONString(streamInfo));
        return response;
    }

    /**
     * 停止
     */
    @RedisRpcMapping("stop")
    public RedisRpcResponse stop(RedisRpcRequest request) {
        int id = Integer.parseInt(request.getParam().toString());
        RedisRpcResponse response = request.getResponse();
        if (id <= 0) {
            response.setStatusCode(ErrorCode.ERROR400.getCode());
            response.setBody("param error");
            return response;
        }
        StreamProxy streamProxy = streamProxyService.getStreamProxy(id);
        if (streamProxy == null) {
            response.setStatusCode(ErrorCode.ERROR400.getCode());
            response.setBody("param error");
            return response;
        }
        streamProxyPlayService.stopProxy(streamProxy);
        response.setStatusCode(ErrorCode.SUCCESS.getCode());
        return response;
    }

}
