package com.basiclab.iot.device.service.device.impl;

import cn.hutool.core.util.StrUtil;
import cn.hutool.json.JSONUtil;
import com.basiclab.iot.sink.biz.IotDownstreamMessageApi;
import com.basiclab.iot.sink.mq.message.IotDeviceMessage;
import com.basiclab.iot.common.constant.Constants;
import com.basiclab.iot.common.domain.R;
import com.basiclab.iot.common.factory.ProtocolMessageAdapter;
import com.basiclab.iot.common.model.EncryptionDetailsDTO;
import com.basiclab.iot.common.model.ProtocolDataMessageDTO;
import com.basiclab.iot.common.mqs.ConsumerTopicConstant;
import com.basiclab.iot.common.utils.SnowflakeIdUtil;
import com.basiclab.iot.common.utils.bean.BeanPlusUtil;
import com.basiclab.iot.device.cache.helper.CacheDataHelper;
import com.basiclab.iot.device.domain.device.vo.*;
import com.basiclab.iot.device.domain.product.vo.result.ProductResultVO;
import com.basiclab.iot.device.enums.device.DeviceCommandStatusEnum;
import com.basiclab.iot.device.enums.device.DeviceCommandTypeEnum;
import com.basiclab.iot.device.dal.pgsql.device.DeviceCommandMapper;
import com.basiclab.iot.device.service.device.DeviceCommandService;
import com.basiclab.iot.device.service.device.DeviceService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.scheduling.annotation.Async;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import javax.annotation.Resource;
import java.util.Collections;
import java.util.List;
import java.util.Optional;

/**
 * <p>
 * 业务实现类
 * 设备命令下发及响应表
 * </p>
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 * @date 2023-10-20 17:27:25
 * @create [2023-10-20 17:27:25] [mqttsnet]
 */
@Slf4j
@RequiredArgsConstructor
@Service
@Transactional(rollbackFor = Exception.class)
public class DeviceCommandServiceImpl implements DeviceCommandService {

    private final CacheDataHelper cacheDataHelper;

    private final ProtocolMessageAdapter protocolMessageAdapter;

    @Resource
    private IotDownstreamMessageApi iotDownstreamMessageApi;

    @Autowired
    private DeviceService deviceService;

    @Autowired
    private DeviceCommandMapper deviceCommandMapper;

    @Override
    public int deleteByPrimaryKey(Long id) {
        return deviceCommandMapper.deleteByPrimaryKey(id);
    }

    @Override
    public int insert(DeviceCommand record) {
        return deviceCommandMapper.insert(record);
    }

    @Override
    public int insertSelective(DeviceCommand record) {
        return deviceCommandMapper.insertSelective(record);
    }

    @Override
    public DeviceCommand selectByPrimaryKey(Long id) {
        return deviceCommandMapper.selectByPrimaryKey(id);
    }

    @Override
    public int updateByPrimaryKeySelective(DeviceCommand record) {
        return deviceCommandMapper.updateByPrimaryKeySelective(record);
    }

    @Override
    public int updateByPrimaryKey(DeviceCommand record) {
        return deviceCommandMapper.updateByPrimaryKey(record);
    }

    /**
     * Saves a device command to the database after validation.
     *
     * @param deviceCommandSaveVO The device command data transfer object.
     * @return The saved DeviceCommand entity.
     * @throws IllegalArgumentException if input validation fails.
     */
    @Override
    public DeviceCommand saveDeviceCommand(DeviceCommandSaveVO deviceCommandSaveVO) {
        // Validate the input, build the DeviceCommand object, and save it to the database.
        return Optional.of(deviceCommandSaveVO).filter(this::checkDeviceCommandSaveVO).map(this::buildDeviceCommand).map(deviceCommand -> {
            deviceCommand.setCommandIdentification(SnowflakeIdUtil.nextId());
            this.insertSelective(deviceCommand);
            return deviceCommand;
        }).orElseThrow(() -> new IllegalArgumentException("Invalid DeviceCommandSaveVO input"));
    }

    /**
     * Fetch a list of device command result VOs.
     *
     * @param query the query parameters
     * @return a list of DeviceCommandResultVOs
     */
    /*@Override
    public List<DeviceCommandResultVO> getDeviceCommandResultVOList(DeviceCommandPageQuery query) {
        return superManager.getDeviceCommandResultVOList(query);
    }*/

    /**
     * Processes both serial and parallel device command requests.
     *
     * @param commandWrapper wrapper containing both serial and parallel command requests
     */
    @Override
    public void processDeviceCommands(DeviceCommandWrapperParam commandWrapper) {
        // Process serial commands
        Optional.ofNullable(commandWrapper.getSerial()).orElseGet(Collections::emptyList).forEach(this::processSingleCommand);

        // Process parallel commands concurrently
        Optional.ofNullable(commandWrapper.getParallel()).orElseGet(Collections::emptyList).parallelStream().forEach(this::processSingleCommand);
    }

    /**
     * Build DeviceCommand from DeviceCommandSaveVO.
     *
     * @param deviceCommandSaveVO input VO object
     * @return DeviceCommand object
     */
    private DeviceCommand buildDeviceCommand(DeviceCommandSaveVO deviceCommandSaveVO) {
        return BeanPlusUtil.toBeanIgnoreError(deviceCommandSaveVO, DeviceCommand.class);
    }

    /**
     * Validate the DeviceCommandSaveVO object.
     *
     * @param deviceCommandSaveVO the input VO to validate
     */
    private Boolean checkDeviceCommandSaveVO(DeviceCommandSaveVO deviceCommandSaveVO) {

        if (StrUtil.isBlank(deviceCommandSaveVO.getDeviceIdentification())) {
            log.warn("Device identification is null");
            return false;
        }

        return true;
    }

    /**
     * Processes a single command request for a device or all devices.
     *
     * @param deviceToGateWayVo The command request parameters.
     */
    @Async("linkAsync-command")
    protected void processSingleCommand(DeviceToGateWayVo deviceToGateWayVo) {
        CommandIssueRequestParam commandRequest = deviceToGateWayVo.getCommandIssueRequestParamVo();
        String productIdentification = commandRequest.getProductIdentification();
        String deviceIdentification = commandRequest.getDeviceIdentification();
        ExtendInfoVo extendInfo = deviceToGateWayVo.getExtendInfo();
        List<DeviceResultVO> deviceResultVOList;

        if (Constants.ALL.equals(deviceIdentification)) {
            // 获取所有设备的结果列表
            deviceResultVOList = getAllDeviceResultVOs(productIdentification);
        } else {
            // 获取单个设备的结果列表
            deviceResultVOList = getSingleDeviceResultVO(deviceIdentification);
        }

        // Process each device command.
        deviceResultVOList.forEach(deviceResultVO -> {
            // Build and send the command message.
            buildAndSendMessage(deviceResultVO, commandRequest, extendInfo);
        });
    }

    /**
     * Retrieves a list of all device result value objects for a specific product.
     *
     * @param productIdentification a product identification string used to find devices.
     * @return A list of DeviceResultVO objects, each representing a device linked to the product.
     */
    private List<DeviceResultVO> getAllDeviceResultVOs(String productIdentification) {
        List<Device> allByProductIdentification = deviceService.findAllByProductIdentification(productIdentification);
        return BeanPlusUtil.copyToList(allByProductIdentification, DeviceResultVO.class);
    }

    /**
     * Retrieves the device result value object for a single device.
     *
     * @param deviceIdentification The device's unique identifier.
     * @return A list containing the single DeviceResultVO.
     */
    private List<DeviceResultVO> getSingleDeviceResultVO(String deviceIdentification) {
        // 获取设备缓存对象
        DeviceCacheVO deviceCacheVO = cacheDataHelper.getDeviceCacheVO(deviceIdentification);

        // 若设备缓存对象为null，则直接返回空列表
        if (deviceCacheVO == null) {
            return Collections.emptyList();
        }

        // 转换设备缓存对象到设备结果VO
        DeviceResultVO deviceResultVO = BeanPlusUtil.toBeanIgnoreError(deviceCacheVO, DeviceResultVO.class);

        // 尝试获取产品缓存VO并转换，然后设置到设备结果VO中
        Optional.ofNullable(deviceCacheVO.getProductCacheVO())
                .map(productCacheVO -> BeanPlusUtil.toBeanIgnoreError(productCacheVO, ProductResultVO.class))
                .ifPresent(deviceResultVO::setProductResultVO);

        // 返回包含一个元素的列表
        return Collections.singletonList(deviceResultVO);
    }

    /**
     * Creates a DeviceCommandSaveVO object based on the command request and response.
     *
     * @param deviceResultVO The device result value object.
     * @param response       The response from the MQTT broker.
     * @return A populated DeviceCommandSaveVO object.
     */
    private DeviceCommandSaveVO createDeviceCommandSaveVO(DeviceResultVO deviceResultVO, R response) {
        DeviceCommandSaveVO deviceCommandSaveVO = new DeviceCommandSaveVO();
        deviceCommandSaveVO.setDeviceIdentification(deviceResultVO.getDeviceIdentification());
        deviceCommandSaveVO.setCommandType(DeviceCommandTypeEnum.COMMAND_ISSUE.getValue());
        if (response.isSuccess()) {
            deviceCommandSaveVO.setStatus(DeviceCommandStatusEnum.SUCCESS.getValue());
            deviceCommandSaveVO.setContent(response.getData().toString());
        } else {
            deviceCommandSaveVO.setStatus(DeviceCommandStatusEnum.FAILURE.getValue());
            deviceCommandSaveVO.setContent(response.getMsg());
        }
        return deviceCommandSaveVO;
    }


    /**
     * Builds and sends a command message to the device.
     *
     * @param deviceResultVO The device result value object.
     * @param commandRequest The command issue request parameters.
     * @param extendInfo
     * @return The response from the MQTT broker.
     */
    private R buildAndSendMessage(DeviceResultVO deviceResultVO, CommandIssueRequestParam commandRequest, ExtendInfoVo extendInfo) {

        // Build the encryption details if all necessary information is present
        //验证标识在产品中设置 考虑签名密钥  不考虑加密密钥
        Optional<EncryptionDetailsDTO> encryptionDetailsOpt = Optional.ofNullable(deviceResultVO).map(drv ->
                EncryptionDetailsDTO.builder()
                        .signKey((drv.getProductResultVO().getSignKey()))
                        .encryptKey((drv.getProductResultVO().getEncryptKey()))
                        .encryptVector(drv.getProductResultVO().getEncryptVector())
                        .cipherFlag(Integer.valueOf(drv.getProductResultVO().getEncryptMethod()))
                        .build());
        // Construct the command message JSON string
        String commandMessageJson = Optional.ofNullable(commandRequest).map(cr -> buildCommandMessage(deviceResultVO,extendInfo,  cr)).map(JSONUtil::toJsonStr).orElse("{}"); // Fallback to an empty JSON object if commandRequest is null

        // Try to build the response using the encryption details
        Optional<ProtocolDataMessageDTO> handleResultOpt = encryptionDetailsOpt.flatMap(encryptionDetails -> {
            try {
                // Attempt to build the response with encryption details and return as an Optional
                return Optional.ofNullable(protocolMessageAdapter.buildResponse(commandMessageJson, encryptionDetails));
            } catch (Exception e) {
                // Log and handle any exceptions that occur during response building
                log.error("Failed to build the response due to an exception.", e);
                return Optional.empty();
            }
        });

        // Prepare the MQTT message content with a default response if handleResult is absent
        String messageContent = handleResultOpt.map(JSONUtil::toJsonStr).orElseGet(() -> {
            // Log the absence of handleResult and use a default empty message
            log.warn("No response object was constructed; using default empty message.");
            return "{}";
        });

        // Send the constructed message using IotDownstreamMessageApi
        try {
            // 构建 IotDeviceMessage
            // 注意：IotDeviceMessage 的 params 字段类型是 Object，可以直接传入 JSON 字符串解析后的对象
            Object params = JSONUtil.parse(messageContent);
            IotDeviceMessage deviceMessage = IotDeviceMessage.builder()
                    .deviceId(deviceResultVO.getId())
                    .topic(ConsumerTopicConstant.Mqtt.IOT_MQS_MQTT_MSG)
                    .params(params)
                    .build();
            
            // 发送下行消息
            iotDownstreamMessageApi.sendDownstreamMessage(deviceMessage);
            
            return R.ok(null, "消息发送成功");
        } catch (Exception e) {
            log.error("Failed to send message using IotDownstreamMessageApi", e);
            return R.fail("消息发送失败: " + e.getMessage());
        }
    }


    /**
     * Generates a response topic string using the provided version and device ID.
     *
     * @param version  The version number.
     * @param deviceId The unique identifier of the device.
     * @return A complete response topic string.
     */
    protected String generateResponseTopic(String version, String deviceId) {
        return String.format("/%s/devices/%s%s", version, deviceId, "/command");
    }


    /**
     * Build command message.
     *
     * @param deviceResultVO device result VO
     * @param extendInfo
     * @param commandRequest command request
     * @return command message
     */
    private String buildCommandMessage(DeviceResultVO deviceResultVO, ExtendInfoVo extendInfo, CommandIssueRequestParam commandRequest) {
        // Adapter logic to build the command message should be placed here.
        commandRequest.setDeviceIdentification(deviceResultVO.getDeviceIdentification());
        //构建kafka消息传输对象
        DeviceToGateWayVo deviceToGateWayVo = DeviceToGateWayVo.builder()
                .commandIssueRequestParamVo(commandRequest)
                .extendInfo(extendInfo)
                .build();
        return JSONUtil.toJsonStr(deviceToGateWayVo);
    }

    /**
     * Sends a message to the specified MQTT topic with the provided QoS and payload.
     * 
     * 注意：此方法已改为使用 IotDownstreamMessageApi，会从 topic 中提取 deviceIdentification 并查找对应的 deviceId。
     *
     * @param topic    The MQTT topic to publish the message to.
     * @param qos      The quality of service for the message.
     * @param message  The payload of the message.
     * @param tenantId The tenant ID.
     * @return The response from the MQTT broker.
     */
    @Override
    public R sendMessage(String topic, String qos, String message, String tenantId) {
        try {
            // 从 topic 中提取 deviceIdentification
            String deviceIdentification = extractDeviceIdentificationFromTopic(topic);
            if (StrUtil.isBlank(deviceIdentification)) {
                log.warn("[sendMessage][无法从 topic 中提取 deviceIdentification，topic: {}]", topic);
                return R.fail("无法从 topic 中提取设备标识");
            }

            // 根据 deviceIdentification 查找设备
            Device device = deviceService.findOneByDeviceIdentification(deviceIdentification);
            if (device == null) {
                log.warn("[sendMessage][设备不存在，deviceIdentification: {}]", deviceIdentification);
                return R.fail("设备不存在: " + deviceIdentification);
            }

            // 构建 IotDeviceMessage
            Object params = JSONUtil.parse(message);
            IotDeviceMessage deviceMessage = IotDeviceMessage.builder()
                    .deviceId(device.getId())
                    .topic(topic)
                    .params(params)
                    .build();

            // 发送下行消息
            iotDownstreamMessageApi.sendDownstreamMessage(deviceMessage);

            return R.ok(null, "消息发送成功");
        } catch (Exception e) {
            log.error("[sendMessage][发送消息失败，topic: {}，错误: {}]", topic, e.getMessage(), e);
            return R.fail("消息发送失败: " + e.getMessage());
        }
    }

    /**
     * 从 topic 中提取 deviceIdentification
     * 
     * 支持的 topic 格式：
     * - /v1/devices/{deviceIdentification}/...
     * - /iot/{productIdentification}/{deviceIdentification}/...
     * 
     * @param topic MQTT topic
     * @return deviceIdentification，如果无法提取则返回 null
     */
    private String extractDeviceIdentificationFromTopic(String topic) {
        if (StrUtil.isBlank(topic)) {
            return null;
        }

        String[] parts = topic.split("/");
        // 格式：/v1/devices/{deviceIdentification}/...
        if (parts.length >= 4 && "v1".equals(parts[1]) && "devices".equals(parts[2])) {
            return parts[3];
        }
        // 格式：/iot/{productIdentification}/{deviceIdentification}/...
        if (parts.length >= 4 && "iot".equals(parts[1])) {
            return parts[3];
        }

        log.warn("[extractDeviceIdentificationFromTopic][无法从 topic 中提取 deviceIdentification，topic: {}]", topic);
        return null;
    }

    @Override
    public R sendCustomMessage(PublishMessageRequestParam publishMessageRequestParam) {
        try {
            // 从 topic 中提取 deviceIdentification
            String deviceIdentification = extractDeviceIdentificationFromTopic(publishMessageRequestParam.getTopic());
            if (StrUtil.isBlank(deviceIdentification)) {
                log.warn("[sendCustomMessage][无法从 topic 中提取 deviceIdentification，topic: {}]", 
                        publishMessageRequestParam.getTopic());
                return R.fail("无法从 topic 中提取设备标识");
            }

            // 根据 deviceIdentification 查找设备
            Device device = deviceService.findOneByDeviceIdentification(deviceIdentification);
            if (device == null) {
                log.warn("[sendCustomMessage][设备不存在，deviceIdentification: {}]", deviceIdentification);
                return R.fail("设备不存在: " + deviceIdentification);
            }

            // 构建 IotDeviceMessage
            Object params = JSONUtil.parse(publishMessageRequestParam.getPayload());
            IotDeviceMessage deviceMessage = IotDeviceMessage.builder()
                    .deviceId(device.getId())
                    .topic(publishMessageRequestParam.getTopic())
                    .params(params)
                    .build();

            // 发送下行消息
            iotDownstreamMessageApi.sendDownstreamMessage(deviceMessage);

            return R.ok(null, "消息发送成功");
        } catch (Exception e) {
            log.error("[sendCustomMessage][发送消息失败，topic: {}，错误: {}]", 
                    publishMessageRequestParam.getTopic(), e.getMessage(), e);
            return R.fail("消息发送失败: " + e.getMessage());
        }
    }


}


