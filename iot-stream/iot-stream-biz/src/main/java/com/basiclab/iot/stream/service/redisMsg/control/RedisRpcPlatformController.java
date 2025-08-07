package com.basiclab.iot.stream.service.redisMsg.control;

import com.alibaba.fastjson2.JSONObject;
import com.basiclab.iot.stream.config.UserSetting;
import com.basiclab.iot.stream.config.redis.RedisRpcConfig;
import com.basiclab.iot.stream.config.redis.bean.RedisRpcMessage;
import com.basiclab.iot.stream.config.redis.bean.RedisRpcRequest;
import com.basiclab.iot.stream.config.redis.bean.RedisRpcResponse;
import com.basiclab.iot.stream.bean.CommonGBChannel;
import com.basiclab.iot.stream.bean.Platform;
import com.basiclab.iot.stream.event.EventPublisher;
import com.basiclab.iot.stream.service.IPlatformChannelService;
import com.basiclab.iot.stream.service.IPlatformService;
import com.basiclab.iot.stream.service.redisMsg.dto.RedisRpcController;
import com.basiclab.iot.stream.service.redisMsg.dto.RedisRpcMapping;
import com.basiclab.iot.stream.service.redisMsg.dto.RpcController;
import com.basiclab.iot.stream.vmanager.bean.ErrorCode;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.data.redis.core.RedisTemplate;
import org.springframework.stereotype.Component;

import java.util.List;

@Component
@Slf4j
@RedisRpcController("platform")
public class RedisRpcPlatformController extends RpcController {

    @Autowired
    private UserSetting userSetting;

    @Autowired
    private RedisTemplate<Object, Object> redisTemplate;

    @Autowired
    private IPlatformService platformService;

    @Autowired
    private IPlatformChannelService platformChannelService;

    @Autowired
    private EventPublisher eventPublisher;


    private void sendResponse(RedisRpcResponse response){
        log.info("[redis-rpc] >> {}", response);
        response.setToId(userSetting.getServerId());
        RedisRpcMessage message = new RedisRpcMessage();
        message.setResponse(response);
        redisTemplate.convertAndSend(RedisRpcConfig.REDIS_REQUEST_CHANNEL_KEY, message);
    }

    /**
     * 更新
     */
    @RedisRpcMapping("update")
    public RedisRpcResponse play(RedisRpcRequest request) {
        Platform platform = JSONObject.parseObject(request.getParam().toString(), Platform.class);
        RedisRpcResponse response = request.getResponse();
        boolean update = platformService.update(platform);
        response.setStatusCode(ErrorCode.SUCCESS.getCode());
        response.setBody(Boolean.toString(update));
        return response;
    }

    /**
     * 目录更新推送
     */
    @RedisRpcMapping("catalogEventPublish")
    public RedisRpcResponse catalogEventPublish(RedisRpcRequest request) {
        JSONObject jsonObject = JSONObject.parseObject(request.getParam().toString());
        Platform platform = jsonObject.getObject("platform", Platform.class);

        List<CommonGBChannel> channels = jsonObject.getJSONArray("channels").toJavaList(CommonGBChannel.class);
        String type = jsonObject.getString("type");
        eventPublisher.catalogEventPublish(platform, channels, type);
        RedisRpcResponse response = request.getResponse();
        response.setStatusCode(ErrorCode.SUCCESS.getCode());
        return response;
    }

}
