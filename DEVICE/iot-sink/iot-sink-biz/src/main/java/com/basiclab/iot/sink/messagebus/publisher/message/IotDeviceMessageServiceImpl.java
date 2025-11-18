package com.basiclab.iot.sink.messagebus.publisher.message;

import cn.hutool.core.lang.Assert;
import cn.hutool.core.util.StrUtil;
import cn.hutool.extra.spring.SpringUtil;
import com.basiclab.iot.common.utils.json.JsonUtils;
import com.basiclab.iot.sink.biz.dto.IotDeviceRespDTO;
import com.basiclab.iot.sink.codec.IotDeviceMessageCodec;
import com.basiclab.iot.sink.javascript.JsScriptManager;
import com.basiclab.iot.sink.mq.message.IotDeviceMessage;
import com.basiclab.iot.sink.mq.producer.IotDeviceMessageProducer;
import com.basiclab.iot.sink.service.device.DeviceService;
import lombok.extern.slf4j.Slf4j;
import org.springframework.context.ApplicationContext;
import org.springframework.stereotype.Service;
import org.springframework.validation.annotation.Validated;

import org.springframework.context.annotation.Lazy;

import javax.annotation.PostConstruct;
import javax.annotation.Resource;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * IotDeviceMessageServiceImpl
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */

@Service
@Validated
@Slf4j
public class IotDeviceMessageServiceImpl implements IotDeviceMessageService {

    @Resource
    private DeviceService deviceService;

    @Resource
    @Lazy
    private IotDeviceMessageProducer deviceMessageProducer;

    @Resource
    private ApplicationContext applicationContext;

    @Resource
    private JsScriptManager jsScriptManager;

    /**
     * 编解码器缓存，key 为 topic 模式，value 为编解码器实例
     */
    private final Map<String, IotDeviceMessageCodec> codecMap = new HashMap<>();

    /**
     * 编解码器列表，用于按顺序匹配
     */
    private final List<IotDeviceMessageCodec> codecList = new ArrayList<>();

    @PostConstruct
    public void init() {
        // 初始化时，从 Spring 容器中获取所有 IotDeviceMessageCodec 的实现类
        Map<String, IotDeviceMessageCodec> codecBeans = applicationContext.getBeansOfType(IotDeviceMessageCodec.class);
        for (IotDeviceMessageCodec codec : codecBeans.values()) {
            String topicPattern = codec.topic();
            if (StrUtil.isNotBlank(topicPattern)) {
                codecMap.put(topicPattern, codec);
                codecList.add(codec);
                log.info("[init][注册编解码器，Topic模式: {}]", topicPattern);
            } else {
                log.warn("[init][编解码器未提供 Topic 模式，跳过注册: {}]", codec.getClass().getName());
            }
        }
    }

    @Override
    public byte[] encodeDeviceMessage(IotDeviceMessage message, String productIdentification, String deviceIdentification) {
        Assert.notNull(message, "消息不能为空");
        Assert.notBlank(productIdentification, "产品唯一标识不能为空");
        Assert.notBlank(deviceIdentification, "设备唯一标识不能为空");
        
        // 1. 构建 topic（如果消息中没有 topic）
        String topic = message.getTopic();
        if (StrUtil.isBlank(topic)) {
            String method = message.getMethod() != null ? message.getMethod() : "unknown";
            topic = "/iot/" + productIdentification + "/" + deviceIdentification + "/" + method;
        }
        
        // 2. 数据下行前置处理：使用 JS 脚本将平台标准化格式转换为设备原始数据
        // 从 topic 中解析 productIdentification
        String[] topicParts = topic.split("/");
        String productId = null;
        if (topicParts.length >= 3) {
            productId = topicParts[2]; // 通常格式为 /iot/{productIdentification}/{deviceIdentification}/...
        }
        
        // 将消息对象转换为 Map（平台标准化格式）
        Map<String, Object> messageMap = JsonUtils.parseObject(JsonUtils.toJsonString(message), Map.class);
        
        // 调用 JS 脚本进行前置处理
        byte[] scriptResult = null;
        if (productId != null) {
            scriptResult = jsScriptManager.invokeProtocolToRawData(productId, topic, messageMap);
        }
        
        // 如果脚本返回了数据，使用脚本处理后的数据；否则使用编解码器编码
        if (scriptResult != null && scriptResult.length > 0) {
            log.debug("[encodeDeviceMessage][使用 JS 脚本处理后的数据，productIdentification: {}，数据长度: {}]", 
                    productId, scriptResult.length);
            return scriptResult;
        }
        
        // 3. 如果脚本没有返回数据，使用编解码器编码
        IotDeviceMessageCodec codec = getCodecByTopic(topic);
        return codec.encode(message);
    }

    @Override
    public IotDeviceMessage decodeDeviceMessage(byte[] bytes, String productIdentification, String deviceIdentification) {
        Assert.notNull(bytes, "待解码数据不能为空");
        Assert.notBlank(productIdentification, "产品唯一标识不能为空");
        Assert.notBlank(deviceIdentification, "设备唯一标识不能为空");
        
        // 构建默认 topic（如果没有提供 topic，使用默认格式）
        String topic = "/iot/" + productIdentification + "/" + deviceIdentification + "/unknown";
        
        // 使用基于 topic 的解码方法
        return decodeDeviceMessageByTopic(bytes, topic);
    }

    /**
     * 根据 Topic 解码消息
     *
     * @param bytes 消息内容
     * @param topic 实际的 Topic
     * @return 解码后的消息内容
     */
    public IotDeviceMessage decodeDeviceMessageByTopic(byte[] bytes, String topic) {
        Assert.notNull(bytes, "待解码数据不能为空");
        Assert.notBlank(topic, "Topic 不能为空");
        
        // 1. 数据上行前置处理：使用 JS 脚本将设备原始数据转换为平台标准化格式
        // 从 topic 中解析 productIdentification
        String[] topicParts = topic.split("/");
        String productId = null;
        if (topicParts.length >= 3) {
            productId = topicParts[2]; // 通常格式为 /iot/{productIdentification}/{deviceIdentification}/...
        }
        
        // 调用 JS 脚本进行前置处理
        byte[] scriptResult = bytes;
        if (productId != null) {
            byte[] result = jsScriptManager.invokeRawDataToProtocol(productId, topic, bytes);
            if (result != null && result.length > 0) {
                log.debug("[decodeDeviceMessageByTopic][使用 JS 脚本处理后的数据，productIdentification: {}，数据长度: {}]", 
                        productId, result.length);
                scriptResult = result;
            }
        }
        
        // 2. 获取编解码器（通过 topic 匹配）
        IotDeviceMessageCodec codec = getCodecByTopic(topic);
        
        // 3. 解码消息
        IotDeviceMessage message = codec.decode(scriptResult);
        
        // 4. 设置 topic 和 needReply
        if (message != null) {
            message.setTopic(topic);
            // 根据 topic 枚举判断是否需要回复
            com.basiclab.iot.sink.enums.IotDeviceTopicEnum topicEnum = 
                    com.basiclab.iot.sink.enums.IotDeviceTopicEnum.matchTopic(topic);
            if (topicEnum != null) {
                message.setNeedReply(topicEnum.isNeedReply());
            }
        }
        
        return message;
    }

    @Override
    public void sendDeviceMessage(IotDeviceMessage message, String productIdentification, String deviceIdentification, String serverId) {
        Assert.notNull(message, "消息不能为空");
        Assert.notBlank(productIdentification, "产品唯一标识不能为空");
        Assert.notBlank(deviceIdentification, "设备唯一标识不能为空");
        Assert.notBlank(serverId, "服务器 ID 不能为空");
        
        // 1. 获取设备信息
        IotDeviceRespDTO device = deviceService.getDevice(productIdentification, deviceIdentification);
        Assert.notNull(device, "设备不存在，productIdentification: {}, deviceIdentification: {}", productIdentification, deviceIdentification);
        
        // 2. 设置设备信息到消息中
        message.setDeviceId(device.getId());
        message.setTenantId(device.getTenantId());
        message.setServerId(serverId);
        
        // 3. 发送消息到网关（用于网关内部处理）
        deviceMessageProducer.sendDeviceMessageToGateway(serverId, message);
        
        // 4. 发送消息到通用设备消息主题（供 iot-broker 模块消费）
        deviceMessageProducer.sendDeviceMessage(message);
    }

    /**
     * 根据 Topic 获取编解码器
     *
     * @param topic 实际的 Topic
     * @return 编解码器实例
     */
    private IotDeviceMessageCodec getCodecByTopic(String topic) {
        // 1. 优先通过 supports() 方法匹配
        for (IotDeviceMessageCodec codec : codecList) {
            if (codec.supports(topic)) {
                return codec;
            }
        }
        
        // 2. 如果未匹配到，尝试通过 topic 枚举匹配
        com.basiclab.iot.sink.enums.IotDeviceTopicEnum topicEnum = 
                com.basiclab.iot.sink.enums.IotDeviceTopicEnum.matchTopic(topic);
        if (topicEnum != null) {
            String topicPattern = topicEnum.getTopicTemplate();
            IotDeviceMessageCodec codec = codecMap.get(topicPattern);
            if (codec != null) {
                return codec;
            }
        }
        
        throw new IllegalArgumentException("不支持的 Topic: " + topic);
    }

}
