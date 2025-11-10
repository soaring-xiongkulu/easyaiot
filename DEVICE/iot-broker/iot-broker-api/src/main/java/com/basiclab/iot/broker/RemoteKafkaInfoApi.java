package com.basiclab.iot.broker;

import com.basiclab.iot.broker.domain.vo.KafkaMessageRequestVO;
import com.basiclab.iot.broker.factory.RemoteKafkaInfoApiFallback;
import com.basiclab.iot.common.constant.ServiceNameConstants;
import com.basiclab.iot.common.domain.R;
import io.swagger.annotations.ApiOperation;
import io.swagger.annotations.ApiParam;
import org.springframework.cloud.openfeign.FeignClient;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;

/**
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 * @desc
 * @created 2025-06-07
 */
@FeignClient(contextId = "RemoteKafkaInfoApi", value = ServiceNameConstants.IOT_BROKER, fallbackFactory = RemoteKafkaInfoApiFallback.class, path = "/kafka")
public interface RemoteKafkaInfoApi {
    /**
     * kafka推送消息接口
     *
     * @param kafkaMessageRequestVO 推送消息请求参数
     * @return {@link R} 结果
     */
    @ApiOperation(value = "kafka推送消息", notes = "根据提供的主题、服务质量等级、保留标志和消息内容推送MQTT消息")
    @PostMapping(value = "/sendMessage", headers = {"Authorization=Bearer 50684d1e14f54af5a36e74bf0bfb30aa"})
    public R<?> sendMessage(@ApiParam(value = "推送消息请求参数", required = true)
                            @RequestBody KafkaMessageRequestVO kafkaMessageRequestVO);


}
