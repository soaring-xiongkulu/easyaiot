package com.basiclab.iot.stream.service.redisMsg.control;

import com.alibaba.fastjson2.JSONObject;
import com.basiclab.iot.stream.config.UserSetting;
import com.basiclab.iot.stream.config.redis.RedisRpcConfig;
import com.basiclab.iot.stream.config.redis.bean.RedisRpcMessage;
import com.basiclab.iot.stream.config.redis.bean.RedisRpcRequest;
import com.basiclab.iot.stream.config.redis.bean.RedisRpcResponse;
import com.basiclab.iot.stream.service.IDeviceService;
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
@RedisRpcController("device")
public class RedisRpcGbDeviceController extends RpcController {

    @Autowired
    private UserSetting userSetting;

    @Autowired
    private RedisTemplate<Object, Object> redisTemplate;

    @Autowired
    private IDeviceService deviceService;



    private void sendResponse(RedisRpcResponse response){
        log.info("[redis-rpc] >> {}", response);
        response.setToId(userSetting.getServerId());
        RedisRpcMessage message = new RedisRpcMessage();
        message.setResponse(response);
        redisTemplate.convertAndSend(RedisRpcConfig.REDIS_REQUEST_CHANNEL_KEY, message);
    }


    /**
     * 目录订阅
     */
    @RedisRpcMapping("subscribeCatalog")
    public RedisRpcResponse subscribeCatalog(RedisRpcRequest request) {
        JSONObject paramJson = JSONObject.parseObject(request.getParam().toString());
        int id = paramJson.getIntValue("id");
        int cycle = paramJson.getIntValue("cycle");

        RedisRpcResponse response = request.getResponse();

        if (id <= 0) {
            response.setStatusCode(ErrorCode.ERROR400.getCode());
            response.setBody("param error");
            return response;
        }
        deviceService.subscribeCatalog(id, cycle);
        response.setStatusCode(ErrorCode.SUCCESS.getCode());
        return response;
    }

    /**
     * 移动位置订阅
     */
    @RedisRpcMapping("subscribeMobilePosition")
    public RedisRpcResponse subscribeMobilePosition(RedisRpcRequest request) {
        JSONObject paramJson = JSONObject.parseObject(request.getParam().toString());
        int id = paramJson.getIntValue("id");
        int cycle = paramJson.getIntValue("cycle");
        int interval = paramJson.getIntValue("interval");

        RedisRpcResponse response = request.getResponse();

        if (id <= 0) {
            response.setStatusCode(ErrorCode.ERROR400.getCode());
            response.setBody("param error");
            return response;
        }
        deviceService.subscribeMobilePosition(id, cycle, interval);
        response.setStatusCode(ErrorCode.SUCCESS.getCode());
        return response;
    }

}
