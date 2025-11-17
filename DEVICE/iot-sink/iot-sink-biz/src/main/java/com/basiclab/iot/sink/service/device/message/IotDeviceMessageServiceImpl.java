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

import javax.annotation.PostConstruct;
import javax.annotation.Resource;
import java.util.HashMap;
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
    private IotDeviceMessageProducer deviceMessageProducer;

    @Resource
    private ApplicationContext applicationContext;

    /**
     * 编解码器缓存，key 为 codecType，value 为编解码器实例
     */
    private final Map<String, IotDeviceMessageCodec> codecMap = new HashMap<>();

    @PostConstruct
    public void init() {
        // 初始化时，从 Spring 容器中获取所有 IotDeviceMessageCodec 的实现类
        Map<String, IotDeviceMessageCodec> codecBeans = applicationContext.getBeansOfType(IotDeviceMessageCodec.class);
        for (IotDeviceMessageCodec codec : codecBeans.values()) {
            String codecType = codec.type();
            if (StrUtil.isNotBlank(codecType)) {
                codecMap.put(codecType, codec);
                log.info("[init][注册编解码器，类型: {}]", codecType);
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
        
        // 2. 获取编解码器类型
        String codecType = device.getCodecType();
        Assert.notBlank(codecType, "设备编解码器类型不能为空，productKey: {}, deviceName: {}", productKey, deviceName);
        
        // 3. 解码消息
        return decodeDeviceMessage(bytes, codecType);
    }

    @Override
    public IotDeviceMessage decodeDeviceMessage(byte[] bytes, String codecType) {
        Assert.notNull(bytes, "待解码数据不能为空");
        Assert.notBlank(codecType, "编解码器类型不能为空");
        
        // 1. 获取编解码器
        IotDeviceMessageCodec codec = getCodec(codecType);
        
        // 2. 解码消息
        return codec.decode(bytes);
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
     * 获取编解码器
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

}
