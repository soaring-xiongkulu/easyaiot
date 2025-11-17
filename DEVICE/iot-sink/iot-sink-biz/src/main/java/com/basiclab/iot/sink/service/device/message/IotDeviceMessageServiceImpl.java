package com.basiclab.iot.sink.service.device.message;

import cn.hutool.core.lang.Assert;
import cn.hutool.core.util.StrUtil;
import cn.hutool.extra.spring.SpringUtil;
import com.basiclab.iot.sink.biz.dto.IotDeviceRespDTO;
import com.basiclab.iot.sink.codec.IotDeviceMessageCodec;
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
        
        // 2. 获取编解码器类型
        String codecType = device.getCodecType();
        Assert.notBlank(codecType, "设备编解码器类型不能为空，productKey: {}, deviceName: {}", productKey, deviceName);
        
        // 3. 编码消息
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
        
        // 2. 获取编解码器类型（向后兼容）
        String codecType = device.getCodecType();
        if (StrUtil.isNotBlank(codecType)) {
            return decodeDeviceMessage(bytes, codecType);
        }
        
        // 3. 如果设备没有指定编解码器类型，抛出异常
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
        
        // 1. 获取编解码器（通过 topic 匹配）
        IotDeviceMessageCodec codec = getCodecByTopic(topic);
        
        // 2. 解码消息
        IotDeviceMessage message = codec.decode(bytes);
        
        // 3. 设置 topic 和 needReply
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
        
        // 3. 发送消息到网关
        deviceMessageProducer.sendDeviceMessageToGateway(serverId, message);
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
