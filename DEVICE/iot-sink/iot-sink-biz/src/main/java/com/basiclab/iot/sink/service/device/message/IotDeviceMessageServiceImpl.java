package com.basiclab.iot.sink.service.device.message;

import cn.hutool.core.lang.Assert;
import cn.hutool.core.util.StrUtil;
import cn.hutool.extra.spring.SpringUtil;
import com.basiclab.iot.common.utils.json.JsonUtils;
import com.basiclab.iot.sink.biz.dto.IotDeviceRespDTO;
import com.basiclab.iot.sink.codec.IotDeviceMessageCodec;
import com.basiclab.iot.sink.javascript.JsScriptManager;
import com.basiclab.iot.sink.mq.message.IotDeviceMessage;
import com.basiclab.iot.sink.mq.producer.IotDeviceMessageProducer;
import com.basiclab.iot.sink.service.device.IotDeviceService;
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
 * IoT 设备消息 Service 实现类
 *
 * @author 翱翔的雄库鲁
 */
@Service
@Validated
@Slf4j
public class IotDeviceMessageServiceImpl implements IotDeviceMessageService {

    @Resource
    private IotDeviceService deviceService;

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
            // 优先使用 topic() 方法
            String topicPattern = codec.topic();
            if (StrUtil.isNotBlank(topicPattern)) {
                codecMap.put(topicPattern, codec);
                codecList.add(codec);
                log.info("[init][注册编解码器，Topic模式: {}]", topicPattern);
            } else {
                // 向后兼容：使用 type() 方法
            String codecType = codec.type();
            if (StrUtil.isNotBlank(codecType)) {
                codecMap.put(codecType, codec);
                    codecList.add(codec);
                log.info("[init][注册编解码器，类型: {}]", codecType);
                }
            }
        }
    }

    @Override
    public byte[] encodeDeviceMessage(IotDeviceMessage message, String productKey, String deviceName) {
        // 1. 获取设备信息
        IotDeviceRespDTO device = deviceService.getDeviceFromCache(productKey, deviceName);
        Assert.notNull(device, "设备不存在，productKey: {}, deviceName: {}", productKey, deviceName);
        
        // 2. 数据下行前置处理：使用 JS 脚本将平台标准化格式转换为设备原始数据
        String productIdentification = productKey; // 使用 productKey 作为 productIdentification
        String topic = message.getTopic();
        if (StrUtil.isBlank(topic)) {
            // 如果没有 topic，尝试构建一个默认的 topic
            topic = "/iot/" + productKey + "/" + deviceName + "/" + (message.getMethod() != null ? message.getMethod() : "unknown");
        }
        
        // 将消息对象转换为 Map（平台标准化格式）
        Map<String, Object> messageMap = JsonUtils.parseObject(JsonUtils.toJsonString(message), Map.class);
        
        // 调用 JS 脚本进行前置处理
        byte[] scriptResult = jsScriptManager.invokeProtocolToRawData(productIdentification, topic, messageMap);
        
        // 如果脚本返回了数据，使用脚本处理后的数据；否则使用原来的编码逻辑
        if (scriptResult != null && scriptResult.length > 0) {
            log.debug("[encodeDeviceMessage][使用 JS 脚本处理后的数据，产品标识: {}，数据长度: {}]", 
                    productIdentification, scriptResult.length);
            return scriptResult;
        }
        
        // 3. 如果脚本没有返回数据，使用原来的编码逻辑
        String codecType = device.getCodecType();
        Assert.notBlank(codecType, "设备编解码器类型不能为空，productKey: {}, deviceName: {}", productKey, deviceName);
        return encodeDeviceMessage(message, codecType);
    }

    @Override
    public byte[] encodeDeviceMessage(IotDeviceMessage message, String codecType) {
        Assert.notNull(message, "消息不能为空");
        Assert.notBlank(codecType, "编解码器类型不能为空");
        
        // 1. 获取编解码器
        IotDeviceMessageCodec codec = getCodec(codecType);
        
        // 2. 编码消息
        return codec.encode(message);
    }

    @Override
    public IotDeviceMessage decodeDeviceMessage(byte[] bytes, String productKey, String deviceName) {
        // 1. 获取设备信息
        IotDeviceRespDTO device = deviceService.getDeviceFromCache(productKey, deviceName);
        Assert.notNull(device, "设备不存在，productKey: {}, deviceName: {}", productKey, deviceName);
        
        // 2. 数据上行前置处理：使用 JS 脚本将设备原始数据转换为平台标准化格式
        String productIdentification = productKey; // 使用 productKey 作为 productIdentification
        String topic = "/iot/" + productKey + "/" + deviceName + "/unknown"; // 默认 topic，实际使用时会被覆盖
        
        // 调用 JS 脚本进行前置处理
        byte[] scriptResult = jsScriptManager.invokeRawDataToProtocol(productIdentification, topic, bytes);
        
        // 如果脚本返回了数据，使用脚本处理后的数据；否则使用原始数据
        byte[] dataToDecode = bytes;
        if (scriptResult != null && scriptResult.length > 0) {
            log.debug("[decodeDeviceMessage][使用 JS 脚本处理后的数据，产品标识: {}，数据长度: {}]", 
                    productIdentification, scriptResult.length);
            dataToDecode = scriptResult;
        }
        
        // 3. 获取编解码器类型（向后兼容）
        String codecType = device.getCodecType();
        if (StrUtil.isNotBlank(codecType)) {
            return decodeDeviceMessage(dataToDecode, codecType);
        }
        
        // 4. 如果设备没有指定编解码器类型，抛出异常
        throw new IllegalArgumentException("设备编解码器类型不能为空，productKey: " + productKey + ", deviceName: " + deviceName);
    }

    @Override
    public IotDeviceMessage decodeDeviceMessage(byte[] bytes, String codecType) {
        Assert.notNull(bytes, "待解码数据不能为空");
        Assert.notBlank(codecType, "编解码器类型不能为空");
        
        // 1. 获取编解码器（向后兼容，使用 type() 方法）
        IotDeviceMessageCodec codec = getCodec(codecType);
        
        // 2. 解码消息
        return codec.decode(bytes);
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
        // 从 topic 中解析 productKey
        String[] topicParts = topic.split("/");
        String productIdentification = null;
        if (topicParts.length >= 3) {
            productIdentification = topicParts[2]; // 通常格式为 /iot/{productKey}/{deviceName}/...
        }
        
        // 调用 JS 脚本进行前置处理
        byte[] scriptResult = bytes;
        if (productIdentification != null) {
            byte[] result = jsScriptManager.invokeRawDataToProtocol(productIdentification, topic, bytes);
            if (result != null && result.length > 0) {
                log.debug("[decodeDeviceMessageByTopic][使用 JS 脚本处理后的数据，产品标识: {}，数据长度: {}]", 
                        productIdentification, result.length);
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
    public void sendDeviceMessage(IotDeviceMessage message, String productKey, String deviceName, String serverId) {
        Assert.notNull(message, "消息不能为空");
        Assert.notBlank(productKey, "产品 Key 不能为空");
        Assert.notBlank(deviceName, "设备名称不能为空");
        Assert.notBlank(serverId, "服务器 ID 不能为空");
        
        // 1. 获取设备信息
        IotDeviceRespDTO device = deviceService.getDeviceFromCache(productKey, deviceName);
        Assert.notNull(device, "设备不存在，productKey: {}, deviceName: {}", productKey, deviceName);
        
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
     * 获取编解码器（通过 codecType，向后兼容）
     *
     * @param codecType 编解码器类型
     * @return 编解码器实例
     */
    private IotDeviceMessageCodec getCodec(String codecType) {
        IotDeviceMessageCodec codec = codecMap.get(codecType);
        if (codec == null) {
            throw new IllegalArgumentException("不支持的编解码器类型: " + codecType);
        }
        return codec;
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
