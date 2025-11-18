package com.basiclab.iot.device.service.device.impl;

import cn.hutool.core.bean.BeanUtil;
import cn.hutool.core.bean.copier.CopyOptions;
import cn.hutool.core.text.CharSequenceUtil;
import com.alibaba.fastjson2.JSON;
import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.basiclab.iot.common.constant.Constants;
import com.basiclab.iot.common.domain.R;
import com.basiclab.iot.common.text.UUID;
import com.basiclab.iot.common.utils.DateUtils;
import com.basiclab.iot.common.utils.SnowflakeIdUtil;
import com.basiclab.iot.common.utils.StringUtils;
import com.basiclab.iot.device.dal.pgsql.device.DeviceInfoMapper;
import com.basiclab.iot.device.domain.device.vo.*;
import com.basiclab.iot.device.enums.device.DeviceConnectStatusEnum;
import com.basiclab.iot.device.enums.device.DeviceEventTypeEnum;
import com.basiclab.iot.device.enums.device.DeviceType;
import com.basiclab.iot.device.enums.device.MqttProtocolTopoStatusEnum;
import com.basiclab.iot.device.service.device.DeviceInfoService;
import com.basiclab.iot.device.service.device.DeviceService;
import com.basiclab.iot.device.service.product.ProductService;
import com.basiclab.iot.device.service.product.ProductServicesService;
import com.basiclab.iot.tdengine.RemoteTdEngineService;
import com.basiclab.iot.tdengine.domain.SelectDto;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import javax.annotation.Resource;
import java.util.*;
import java.util.concurrent.atomic.AtomicReference;
import java.util.stream.Collectors;
import java.util.stream.Stream;

/**
 * DeviceInfoServiceImpl
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Service
@Slf4j
public class DeviceInfoServiceImpl extends ServiceImpl<DeviceInfoMapper, DeviceInfo> implements DeviceInfoService {
    @Autowired
    private DeviceService deviceService;
    @Autowired
    private ProductService productService;
    @Autowired
    private ProductServicesService productServicesService;
    @Resource
    private RemoteTdEngineService remoteTdEngineService;

    @Value("${spring.datasource.dynamic.datasource.master.dbName:iot}")
    private String dataBaseName;

    @Override
    public int deleteByDeviceId(String deviceId) {
        return baseMapper.deleteByDeviceId(deviceId);
    }

    @Override
    public DeviceInfo findOneByDeviceId(String deviceId) {
        return baseMapper.findOneByDeviceId(deviceId);
    }

    /**
     * 查询子设备管理
     *
     * @param id 子设备管理主键
     * @return 子设备管理
     */
    @Override
    public DeviceInfo selectDeviceInfoById(Long id) {
        DeviceInfo deviceInfo = baseMapper.selectDeviceInfoById(id);
        if (StringUtils.isNotNull(deviceInfo)) {
            Device oneById = deviceService.findOneById(deviceInfo.getDeviceIdentification());
            deviceInfo.setEdgeDevicesIdentification(StringUtils.isNotNull(oneById) ? oneById.getDeviceIdentification() : "");
        }
        return deviceInfo;
    }

    /**
     * 查询子设备管理列表
     *
     * @param deviceInfo 子设备管理
     * @return 子设备管理
     */
    @Override
    public List<DeviceInfo> selectDeviceInfoList(DeviceInfo deviceInfo) {
        List<DeviceInfo> deviceInfoList = baseMapper.selectDeviceInfoList(deviceInfo);
        deviceInfoList.forEach(deviceInfo1 -> {
            Device oneById = deviceService.findOneById(deviceInfo1.getDeviceIdentification());
            deviceInfo1.setEdgeDevicesIdentification(StringUtils.isNotNull(oneById) ? oneById.getDeviceIdentification() : "");
        });
        return deviceInfoList;
    }

    /**
     * 新增子设备管理
     *
     * @param deviceInfoParams 子设备管理
     * @return 结果
     */
    @Override
    public int insertDeviceInfo(DeviceInfoParams deviceInfoParams) {
        DeviceInfo deviceInfo = new DeviceInfo();
        deviceInfo.convertEntity(deviceInfoParams);
        deviceInfo.setCreateBy("admin");
        deviceInfo.setDeviceId(UUID.getUUID());
        deviceInfo.setConnectStatus(DeviceConnectStatusEnum.INIT.getValue());
        deviceInfo.setShadowEnable(true);
        return baseMapper.insertDeviceInfo(deviceInfo);
    }

    /**
     * 修改子设备管理
     *
     * @param deviceInfoParams 子设备管理
     * @return 结果
     */
    @Override
    public int updateDeviceInfo(DeviceInfoParams deviceInfoParams) {
        DeviceInfo deviceInfo = baseMapper.selectById(deviceInfoParams.getId());
        deviceInfo.convertEntity(deviceInfoParams);
        deviceInfo.setUpdateBy("admin");
        return baseMapper.updateDeviceInfo(deviceInfo);
    }

    /**
     * 批量删除子设备管理
     *
     * @param ids 需要删除的子设备管理主键
     * @return 结果
     */
    @Override
    public int deleteDeviceInfoByIds(Long[] ids) {
        AtomicReference<Integer> deleteCount = new AtomicReference<>(0);
        baseMapper.findAllByIdIn(Arrays.asList(ids)).forEach(deviceInfo -> {
            Map<String, Object> responseMaps = new HashMap<>();
            List<Map<String, Object>> dataList = new ArrayList<>();
            responseMaps.put("mid", 1);
            responseMaps.put("statusCode", 0);
            responseMaps.put("statusDesc", "successful");
            responseMaps.put("data", dataList);
            final int deleteByDeviceIdCount = this.deleteByDeviceId(deviceInfo.getDeviceId());
            Map<String, Object> responseMap = new HashMap<>();
            if (deleteByDeviceIdCount > 0) {
                responseMap.put("statusCode", 0);
                responseMap.put("statusDesc", "successful");
                deleteCount.getAndSet(deleteCount.get() + 1);
            } else {
                responseMap.put("statusCode", 1);
                responseMap.put("statusDesc", "abortive");
                log.error("Delete DeviceInfo Exception");
            }
            responseMap.put("deviceId", deviceInfo.getDeviceId());
            dataList.add(responseMap);
            Device device = deviceService.findOneById(deviceInfo.getDeviceIdentification());
            if (StringUtils.isNotNull(device)) {
                final Map<String, Object> param = new HashMap<>();
                param.put("topic", "/v1/devices/" + device.getDeviceIdentification() + "/topo/deleteResponse");
                param.put("qos", 2);
                param.put("retain", false);
                param.put("message", JSON.toJSONString(responseMaps));
//                remoteMqttBrokerOpenApi.sendMessage(param);
            }
            responseMaps.clear();
        });
        return deleteCount.get();
    }

    /**
     * 查询子设备影子数据
     *
     * @param ids       需要查询的子设备id
     * @param startTime 开始时间 格式：yyyy-MM-dd HH:mm:ss
     * @param endTime   结束时间 格式：yyyy-MM-dd HH:mm:ss
     * @return 子设备影子数据
     */
    @Override
    public Map<String, List<Map<String, Object>>> getDeviceInfoShadow(String ids, String startTime, String endTime) {
        List<Long> idCollection = Arrays.stream(ids.split(",")).mapToLong(Long::parseLong).boxed().collect(Collectors.toList());
        List<DeviceInfo> deviceInfos = baseMapper.findAllByIdInAndStatus(idCollection, Constants.ENABLE);
        if (StringUtils.isNull(deviceInfos)) {
            log.error("查询子设备影子数据失败，子设备不存在");
            return null;
        }
        Map<String, List<Map<String, Object>>> map = new HashMap<>();
        deviceInfos.forEach(deviceInfo -> {
            if (StringUtils.isNull(deviceInfo.getShadowTableName())) {
                log.error("查询子设备影子数据失败，子设备影子表名为空");
                return;
            }
            List<String> shadowTableNameCollect = Stream.of(deviceInfo.getShadowTableName().split(",")).collect(Collectors.toList());
            shadowTableNameCollect.forEach(shadowTableName -> {
                SelectDto selectDto = new SelectDto();
                selectDto.setDataBaseName(dataBaseName);
                selectDto.setTableName(shadowTableName);
                if (StringUtils.isNotEmpty(startTime) && StringUtils.isNotEmpty(endTime)) {
                    selectDto.setFieldName("ts");
                    selectDto.setStartTime(DateUtils.localDateTime2Millis(DateUtils.dateToLocalDateTime(DateUtils.strToDate(startTime))));
                    selectDto.setEndTime(DateUtils.localDateTime2Millis(DateUtils.dateToLocalDateTime(DateUtils.strToDate(endTime))));
                    R<?> dataByTimestamp = remoteTdEngineService.getDataByTimestamp(selectDto);
                    if (StringUtils.isNull(dataByTimestamp)) {
                        log.error("查询子设备影子数据失败，子设备影子数据不存在");
                    } else {
                        map.put(shadowTableName, (List<Map<String, Object>>) dataByTimestamp.getData());
                        log.info("查询子设备影子数据成功，子设备影子数据：{}", dataByTimestamp.getData());

                    }
                } else {
                    R<?> lastData = remoteTdEngineService.getLastData(selectDto);
                    if (StringUtils.isNull(lastData)) {
                        log.error("查询子设备影子数据失败，子设备影子数据不存在");
                    } else {
                        map.put(shadowTableName, (List<Map<String, Object>>) lastData.getData());
                        log.info("查询子设备影子数据成功，子设备影子数据：{}", lastData.getData());

                    }
                }

            });
        });
        return map;
    }

    @Override
    public List<DeviceInfo> findAllByIdInAndStatus(Collection<Long> idCollection, String status) {
        return baseMapper.findAllByIdInAndStatus(idCollection, status);
    }

    @Override
    public List<DeviceInfo> findAllByIdIn(Collection<Long> idCollection) {
        return baseMapper.findAllByIdIn(idCollection);
    }

    @Override
    public List<DeviceInfo> findAllByStatus(String status) {
        return baseMapper.findAllByStatus(status);
    }

    /**
     * 添加网关子设备
     *
     * @param topoAddSubDeviceParam TopoAddDeviceParam，添加设备的参数信息
     * @return {@link TopoAddDeviceResultVO} 添加设备的结果信息
     */
    private TopoAddDeviceResultVO saveSubDevice(TopoAddSubDeviceParam topoAddSubDeviceParam) {

        // 根据网关ID查找网关设备
        Device gatewayDevice = deviceService.findOneByDeviceIdentification(topoAddSubDeviceParam.getGatewayIdentification());
        Product product = productService.selectByProductIdentification(gatewayDevice.getProductIdentification());
        // 假设 gatewayDevice.getType() 方法返回设备类型，且 DeviceType.GATEWAY 代表网关设备类型
        MqttProtocolTopoStatusEnum statusEnum = MqttProtocolTopoStatusEnum.FAILURE;

        if (DeviceType.GATEWAY.getValue().equals(product.getProductType())) {
            statusEnum = MqttProtocolTopoStatusEnum.SUCCESS;
        } else {
            statusEnum = MqttProtocolTopoStatusEnum.FAILURE;
        }

        // 创建返回结果实例并设置状态码和状态描述
        TopoAddDeviceResultVO mqttTopoAddDeviceResultVO = TopoAddDeviceResultVO.builder()
                .statusCode(statusEnum.getValue())
                .statusDesc(statusEnum.getDesc())
                .build();

        // 创建一个设备列表用于存储处理结果
        List<TopoAddDeviceResultVO.DataItem> deviceList = new ArrayList<>();

        // 检查设备信息列表是否为空
        List<TopoAddSubDeviceParam.DeviceInfos> deviceInfos = topoAddSubDeviceParam.getDeviceInfos();
        if (!deviceInfos.isEmpty() && MqttProtocolTopoStatusEnum.SUCCESS.equals(statusEnum)) {
            // 遍历添加设备的参数信息列表
            for (TopoAddSubDeviceParam.DeviceInfos item : deviceInfos) {
                try {
                    // 创建数据项实例并验证设备参数
                    TopoAddDeviceResultVO.DataItem dataItem = new TopoAddDeviceResultVO.DataItem();
                    checkedTopoAddDeviceParam(item, dataItem);
                    // 将参数对象转换为设备信息对象并设置到数据项中
                    dataItem.setDeviceInfo(BeanUtil.toBean(item, TopoAddDeviceResultVO.DataItem.DeviceInfo.class, CopyOptions.create().ignoreError()));

                    // 如果设备参数验证不通过，添加到设备列表并继续下一次循环
                    if (!MqttProtocolTopoStatusEnum.SUCCESS.getValue().equals(dataItem.getStatusCode())) {
                        deviceList.add(dataItem);
                        continue;
                    }

                    // 转换并保存子设备信息
                    DeviceInfoParams deviceInfoParams = conversionDeviceBySaveSubDevice(gatewayDevice, item);
                    int insertCount = this.insertDeviceInfo(deviceInfoParams);

                    // TODO 存储子设备经纬度信息
                    /*DeviceLocationPageQuery deviceLocationPageQuery = new DeviceLocationPageQuery();
                    deviceLocationPageQuery.setDeviceIdentification(gatewayDevice.getDeviceIdentification());

                    List<DeviceLocationResultVO> deviceLocationResultVOList = deviceLocationService.getDeviceLocationResultVOList(deviceLocationPageQuery);

                    Optional.ofNullable(deviceLocationResultVOList)
                            .filter(list -> !list.isEmpty())
                            .map(list -> list.get(0))
                            .map(deviceLocationResultVO -> BeanPlusUtil.toBeanIgnoreError(deviceLocationResultVO, DeviceLocationSaveVO.class))
                            .ifPresent(deviceLocationSaveVO -> {
                                deviceLocationSaveVO.setDeviceIdentification(subDeviceDO.getDeviceIdentification());
                                deviceLocationService.saveDeviceLocation(deviceLocationSaveVO);
                            });*/

                    // 设置平台生成的设备标识
                    dataItem.getDeviceInfo().setDeviceId(deviceInfoParams.getDeviceId());

                    // 根据保存结果设置状态码和状态描述
                    MqttProtocolTopoStatusEnum saveStatusEnum = insertCount > 0 ? MqttProtocolTopoStatusEnum.SUCCESS : MqttProtocolTopoStatusEnum.FAILURE;
                    dataItem.setStatusCode(saveStatusEnum.getValue())
                            .setStatusDesc(saveStatusEnum.getDesc());

                    // 添加数据项到设备列表
                    deviceList.add(dataItem);
                } catch (Exception e) {
                    // 处理异常情况，将异常信息设置到数据项中
                    TopoAddDeviceResultVO.DataItem dataItem = new TopoAddDeviceResultVO.DataItem();
                    dataItem.setStatusCode(MqttProtocolTopoStatusEnum.FAILURE.getValue())
                            .setStatusDesc(e.getMessage());
                    deviceList.add(dataItem);
                }
            }
        }

        // 将设备列表设置到返回结果实例中
        mqttTopoAddDeviceResultVO.setData(deviceList);
        return mqttTopoAddDeviceResultVO;
    }

    /**
     * 添加网关子设备转换DO Device
     *
     * @param deviceDO 网关设备信息
     * @param item     子设备信息
     * @return {@link DeviceInfoParams} 子设备信息
     */
    private DeviceInfoParams conversionDeviceBySaveSubDevice(Device deviceDO, TopoAddSubDeviceParam.DeviceInfos item) {
        DeviceInfoParams deviceInfoParams = new DeviceInfoParams();
        deviceInfoParams.setAppId(deviceDO.getAppId());
        deviceInfoParams.setDeviceIdentification(deviceDO.getId());
        deviceInfoParams.setDeviceId(SnowflakeIdUtil.nextId());
        deviceInfoParams.setNodeId(item.getNodeId());
        deviceInfoParams.setNodeName(item.getName());
        deviceInfoParams.setManufacturerId(item.getManufacturerId());
        deviceInfoParams.setModel(item.getModel());
        deviceInfoParams.setDescription(item.getDescription());
        deviceInfoParams.setConnectStatus(DeviceConnectStatusEnum.INIT.getValue());
        deviceInfoParams.setShadowEnable(true);
        return deviceInfoParams;
    }

    /**
     * 验证Topo添加设备参数，并设置对应的状态码和状态描述。
     *
     * @param item     TopoAddDeviceParam.DeviceInfos，添加设备的参数信息
     * @param dataItem MqttTopoAddDeviceResultVO.DataItem，用于存储设备添加结果的数据项
     */
    private void checkedTopoAddDeviceParam(TopoAddSubDeviceParam.DeviceInfos item,
                                           TopoAddDeviceResultVO.DataItem dataItem) {
        // 根据设备标识查找子设备
        Device subDevice = deviceService.findOneByDeviceIdentification(item.getNodeId());
        // 用于拼接错误消息的StringBuilder
        StringBuilder errorMessage = new StringBuilder();

        // 检查各参数是否为空，并将错误消息追加到StringBuilder中
        appendErrorMessageIfEmpty(errorMessage, item.getName(), "name is null; ");
        appendErrorMessageIfEmpty(errorMessage, item.getNodeId(), "nodeId is null; ");
        appendErrorMessageIfEmpty(errorMessage, item.getManufacturerId(), "manufacturerId is null; ");
        appendErrorMessageIfEmpty(errorMessage, item.getModel(), "model is null; ");

        // 检查设备节点ID是否已经存在
        if (subDevice != null) {
            errorMessage.append("nodeId is exist; ");
        }

        // 根据错误消息长度判断是否有错误，并设置相应的状态码和状态描述
        if (errorMessage.length() > 0) {
            dataItem.setStatusCode(MqttProtocolTopoStatusEnum.FAILURE.getValue())
                    .setStatusDesc(errorMessage.toString());
        } else {
            dataItem.setStatusCode(MqttProtocolTopoStatusEnum.SUCCESS.getValue())
                    .setStatusDesc(MqttProtocolTopoStatusEnum.SUCCESS.getDesc());
        }
    }

    /**
     * 检查参数值是否为空，如果为空，将错误消息追加到StringBuilder中。
     *
     * @param errorMessage StringBuilder，用于拼接错误消息
     * @param value        CharSequence，待检查的参数值
     * @param message      String，错误消息
     */
    private void appendErrorMessageIfEmpty(StringBuilder errorMessage, CharSequence value, String message) {
        if (CharSequenceUtil.isEmpty(value)) {
            errorMessage.append(message);
        }
    }

    /**
     * Processes the status of a single sub-device, updates it, and logs the event.
     *
     * @param subDeviceStatus the status of the sub-device to be processed
     * @return an operation response object for the sub-device
     */
    private TopoDeviceOperationResultVO.OperationRsp processSubDeviceStatus(TopoUpdateSubDeviceStatusParam.DeviceStatus subDeviceStatus) {
        DeviceInfo deviceInfo = this.findOneByDeviceId(subDeviceStatus.getDeviceId());
        TopoDeviceOperationResultVO.OperationRsp dataItem = new TopoDeviceOperationResultVO.OperationRsp()
                .setDeviceId(subDeviceStatus.getDeviceId());

        if (deviceInfo != null) {
            deviceInfo.setConnectStatus(subDeviceStatus.getStatus().getValue());
            int updateCount = baseMapper.updateById(deviceInfo);
            MqttProtocolTopoStatusEnum updateStatusEnum = updateCount > 0 ? MqttProtocolTopoStatusEnum.SUCCESS : MqttProtocolTopoStatusEnum.FAILURE;
            dataItem.setStatusCode(updateStatusEnum.getValue())
                    .setStatusDesc(updateStatusEnum.getDesc());
        } else {
            dataItem.setStatusCode(MqttProtocolTopoStatusEnum.FAILURE.getValue())
                    .setStatusDesc(MqttProtocolTopoStatusEnum.FAILURE.getDesc());
        }

        return dataItem;
    }

    /**
     * Determines the event type based on the device connection status.
     *
     * @param status the device connection status
     * @return the corresponding event type
     */
    private DeviceEventTypeEnum getEventTypeForStatus(DeviceConnectStatusEnum status) {
        if (DeviceConnectStatusEnum.OFFLINE.equals(status)) {
            return DeviceEventTypeEnum.CLOSE;
        } else if (DeviceConnectStatusEnum.ONLINE.equals(status)) {
            return DeviceEventTypeEnum.CONNECT;
        } else {
            // Handle unexpected status here
            log.warn("Unexpected status: {}", status);
            return DeviceEventTypeEnum.UNKNOWN;
        }
    }

    /**
     * Gets a descriptive text based on the device connection status.
     *
     * @param status the device connection status
     * @return a string description for the status
     */
    private String getDescriptionForStatus(DeviceConnectStatusEnum status) {
        String desc = Optional.ofNullable(status)
                .map(DeviceConnectStatusEnum::getValue)
                .orElse("Unknown Status");

        return "The device connection status is updated to " + desc;
    }

    private TopoDeviceOperationResultVO deleteSubDevice(TopoDeleteSubDeviceParam topoDeleteSubDeviceParam) {
        // 创建一个操作结果列表用于存储处理结果
        List<TopoDeviceOperationResultVO.OperationRsp> operationResultList = new ArrayList<>();

        // 遍历子设备标识集合
        for (String deviceId : topoDeleteSubDeviceParam.getDeviceIds()) {
            // 根据子设备唯一标识查找设备
            DeviceInfo deviceInfo = this.findOneByDeviceId(deviceId);

            // 创建操作结果实例
            TopoDeviceOperationResultVO.OperationRsp operationRsp = new TopoDeviceOperationResultVO.OperationRsp()
                    .setDeviceId(deviceId);

            // 判断设备是否存在
            if (deviceInfo != null) {
                // 删除设备
                int deleteCount = baseMapper.deleteByDeviceId(deviceInfo.getDeviceId());

                // 根据删除结果设置状态码和状态描述
                MqttProtocolTopoStatusEnum deleteStatusEnum = deleteCount > 0 ? MqttProtocolTopoStatusEnum.SUCCESS : MqttProtocolTopoStatusEnum.FAILURE;
                operationRsp.setStatusCode(deleteStatusEnum.getValue())
                        .setStatusDesc(deleteStatusEnum.getDesc());
            } else {
                // 如果设备不存在，设置状态码和状态描述为FAILURE
                operationRsp.setStatusCode(MqttProtocolTopoStatusEnum.FAILURE.getValue())
                        .setStatusDesc(MqttProtocolTopoStatusEnum.FAILURE.getDesc());
            }

            // 添加操作结果到操作结果列表
            operationResultList.add(operationRsp);
        }

        // 创建返回结果实例并设置状态码、状态描述和操作结果列表
        return TopoDeviceOperationResultVO.builder()
                .statusCode(MqttProtocolTopoStatusEnum.SUCCESS.getValue())
                .statusDesc(MqttProtocolTopoStatusEnum.SUCCESS.getDesc())
                .data(operationResultList)
                .build();
    }

}
