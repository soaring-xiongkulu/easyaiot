package com.basiclab.iot.device.service.device.impl;

import cn.hutool.core.bean.BeanUtil;
import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.basiclab.iot.broker.RemoteMqttBrokerOpenApi;
import com.basiclab.iot.common.constant.CacheConstants;
import com.basiclab.iot.common.domain.R;
import com.basiclab.iot.common.enums.ResultEnum;
import com.basiclab.iot.common.service.RedisService;
import com.basiclab.iot.common.utils.DateUtils;
import com.basiclab.iot.common.utils.StringUtils;
import com.basiclab.iot.common.utils.bean.BeanPlusUtil;
import com.basiclab.iot.device.domain.device.vo.*;
import com.basiclab.iot.device.enums.device.DeviceConnectStatusEnum;
import com.basiclab.iot.device.enums.device.DeviceTopicEnum;
import com.basiclab.iot.device.enums.device.DeviceType;
import com.basiclab.iot.device.enums.device.MqttProtocolTopoStatusEnum;
import com.basiclab.iot.device.mapper.device.DeviceMapper;
import com.basiclab.iot.device.service.device.DeviceLocationService;
import com.basiclab.iot.device.service.device.DeviceService;
import com.basiclab.iot.device.service.device.DeviceTopicService;
import com.basiclab.iot.device.service.product.ProductService;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.BeanUtils;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Isolation;
import org.springframework.transaction.annotation.Propagation;
import org.springframework.transaction.annotation.Transactional;

import javax.annotation.Resource;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.util.*;
import java.util.concurrent.TimeUnit;
import java.util.stream.Collectors;

import static com.basiclab.iot.common.utils.StringUtils.isEmpty;

/**
 * @Description: 设备管理业务层接口实现类
 * @author: EasyAIoT
 * @email: andywebjava@163.com
 */
@Service
@Slf4j
@Transactional(isolation = Isolation.DEFAULT, propagation = Propagation.REQUIRES_NEW, rollbackFor = Exception.class)
public class DeviceServiceImpl implements DeviceService {

    @Resource
    private DeviceMapper deviceMapper;
    @Autowired
    private RedisService redisService;
    @Resource
    private RemoteMqttBrokerOpenApi remoteMqttBrokerOpenApi;
    @Autowired
    private DeviceTopicService deviceTopicService;
    @Autowired
    private ProductService productService;
    @Autowired
    private DeviceLocationService deviceLocationService;

    @Value("${spring.datasource.dynamic.datasource.master.dbName:easyaiot}")
    private String dataBaseName;

    @Override
    public int deleteByPrimaryKey(Long id) {
        return deviceMapper.deleteByPrimaryKey(id);
    }

    @Override
    public int insert(Device record) {
        record.setCreateBy("admin");
        return deviceMapper.insert(record);
    }

    @Override
    public int insertOrUpdate(Device record) {
        record.setCreateBy("admin");
        record.setUpdateBy("admin");
        return deviceMapper.insertOrUpdate(record);
    }

    @Override
    public int insertOrUpdateSelective(Device record) {
        record.setCreateBy("admin");
        record.setUpdateBy("admin");
        return deviceMapper.insertOrUpdateSelective(record);
    }

    @Override
    public int insertSelective(Device record) {
        record.setCreateBy("admin");
        return deviceMapper.insertSelective(record);
    }

    @Override
    public Device selectByPrimaryKey(Long id) {
        return deviceMapper.selectByPrimaryKey(id);
    }

    @Override
    public int updateByPrimaryKeySelective(Device record) {
        record.setUpdateBy("admin");
        return deviceMapper.updateByPrimaryKeySelective(record);
    }

    @Override
    public int updateByPrimaryKey(Device record) {
        record.setUpdateBy("admin");
        return deviceMapper.updateByPrimaryKey(record);
    }

    @Override
    public int updateBatch(List<Device> list) {
        return deviceMapper.updateBatch(list);
    }

    @Override
    public int updateBatchSelective(List<Device> list) {
        return deviceMapper.updateBatchSelective(list);
    }


    @Override
    public int updateConnectStatusByClientId(String updatedConnectStatus, String clientId) {
        log.info("更新设备连接状态为: {} , clientId: {}", updatedConnectStatus, clientId);
        return deviceMapper.updateConnectStatusByClientId(updatedConnectStatus, clientId);
    }


    @Override
    public Device findOneByClientIdAndUserNameAndPasswordAndDeviceStatusAndProtocolType(String clientId, String userName, String password, String deviceStatus, String protocolType) {
        return deviceMapper.findOneByClientIdAndUserNameAndPasswordAndDeviceStatusAndProtocolType(clientId, userName, password, deviceStatus, protocolType);
    }

    @Override
    public Device findOneById(Long id) {
        return deviceMapper.findOneById(id);
    }

    /**
     * 查询设备管理
     *
     * @param id 设备管理主键
     * @return 设备管理
     */
    @Override
    public Device selectDeviceById(Long id) {
        return deviceMapper.selectDeviceById(id);
    }

    /**
     * 查询设备管理列表
     *
     * @param device 设备管理
     * @return 设备管理
     */
    @Override
    public List<Device> selectDeviceList(Device device) {
        return deviceMapper.selectDeviceList(device);
    }

    /**
     * 新增设备管理
     *
     * @param deviceParams 设备管理
     * @return 结果
     */
    @Override
    @Transactional(propagation = Propagation.REQUIRES_NEW, rollbackFor = Exception.class)
    public int insertDevice(Device deviceParams) throws Exception {
        Device device = new Device();
        BeanUtils.copyProperties(deviceParams, device);
        device.setConnectStatus(DeviceConnectStatusEnum.INIT.getValue());
        device.setCreateBy("admin");
        final int insertDeviceCount = deviceMapper.insertOrUpdateSelective(device);
        if (insertDeviceCount > 0) {
            //基础TOPIC集合
            Map<String, String> topicMap = new HashMap<>();
            if (DeviceType.GATEWAY.getValue().equals(device.getDeviceType())) {
                topicMap.put("/" + "v1" + "/devices/" + device.getDeviceIdentification() + "/topo/add", "边设备添加子设备");
                topicMap.put("/" + "v1" + "/devices/" + device.getDeviceIdentification() + "/topo/addResponse", "物联网平台返回的添加子设备的响应");
                topicMap.put("/" + "v1" + "/devices/" + device.getDeviceIdentification() + "/topo/delete", "边设备删除子设备");
                topicMap.put("/" + "v1" + "/devices/" + device.getDeviceIdentification() + "/topo/deleteResponse", "物联网平台返回的删除子设备的响应");
                topicMap.put("/" + "v1" + "/devices/" + device.getDeviceIdentification() + "/topo/update", "边设备更新子设备状态");
                topicMap.put("/" + "v1" + "/devices/" + device.getDeviceIdentification() + "/topo/updateResponse", "物联网平台返回的更新子设备状态的响应");
                topicMap.put("/" + "v1" + "/devices/" + device.getDeviceIdentification() + "/datas", "边设备上报数据");
                topicMap.put("/" + "v1" + "/devices/" + device.getDeviceIdentification() + "/command", "物联网平台给设备或边设备下发命令");
                topicMap.put("/" + "v1" + "/devices/" + device.getDeviceIdentification() + "/commandResponse", "边设备返回给物联网平台的命令响应");

                // 添加OTA更新命令和响应
                topicMap.put("/" + "v1" + "/devices/" + device.getDeviceIdentification() + "/topo/otaCommand", "物联网平台给网关设备下发OTA远程升级命令");
                topicMap.put("/" + "v1" + "/devices/" + device.getDeviceIdentification() + "/topo/otaCommandResponse", "网关设备返回给物联网平台的OTA远程升级命令响应");

                // 添加OTA拉取命令和响应
                topicMap.put("/" + "v1" + "/devices/" + device.getDeviceIdentification() + "/topo/otaPull", "网关设备拉取物联网平台的最新软固件信息");
                topicMap.put("/" + "v1" + "/devices/" + device.getDeviceIdentification() + "/topo/otaPullResponse", "物联网平台响应软固件信息给设备");

                // 添加OTA上报命令和响应
                topicMap.put("/" + "v1" + "/devices/" + device.getDeviceIdentification() + "/topo/otaReport", "网关设备向物联网平台上报软固件版本");
                topicMap.put("/" + "v1" + "/devices/" + device.getDeviceIdentification() + "/topo/otaReportResponse", "物联网平台接收到上报软固件信息响应");

                // 添加OTA读取命令和响应
                topicMap.put("/" + "v1" + "/devices/" + device.getDeviceIdentification() + "/topo/otaRead", "物联网平台读取设备软固件版本");
                topicMap.put("/" + "v1" + "/devices/" + device.getDeviceIdentification() + "/topo/otaReadResponse", "网关设备回复物联网平台读取设备固件版本指令");

            } else if (DeviceType.COMMON.getValue().equals(device.getDeviceType())) {
                topicMap.put("/" + "v1" + "/devices/" + device.getDeviceIdentification() + "/datas", "普通设备上报数据");
                topicMap.put("/" + "v1" + "/devices/" + device.getDeviceIdentification() + "/command", "物联网平台给普通设备下发命令");
                topicMap.put("/" + "v1" + "/devices/" + device.getDeviceIdentification() + "/commandResponse", "普通设备返回给物联网平台的命令响应");
                // 添加OTA更新命令和响应
                topicMap.put("/" + "v1" + "/devices/" + device.getDeviceIdentification() + "/topo/otaCommand", "物联网平台给普通设备下发OTA远程升级命令");
                topicMap.put("/" + "v1" + "/devices/" + device.getDeviceIdentification() + "/topo/otaCommandResponse", "普通设备返回给物联网平台的OTA远程升级命令响应");

                // 添加OTA拉取命令和响应
                topicMap.put("/" + "v1" + "/devices/" + device.getDeviceIdentification() + "/topo/otaPull", "普通设备拉取物联网平台的最新软固件信息");
                topicMap.put("/" + "v1" + "/devices/" + device.getDeviceIdentification() + "/topo/otaPullResponse", "物联网平台响应软固件信息给普通设备");

                // 添加OTA上报命令和响应
                topicMap.put("/" + "v1" + "/devices/" + device.getDeviceIdentification() + "/topo/otaReport", "普通设备向物联网平台上报软固件版本");
                topicMap.put("/" + "v1" + "/devices/" + device.getDeviceIdentification() + "/topo/otaReportResponse", "物联网平台接收到上报软固件信息响应");

                // 添加OTA读取命令和响应
                topicMap.put("/" + "v1" + "/devices/" + device.getDeviceIdentification() + "/topo/otaRead", "物联网平台读取设备软固件版本");
                topicMap.put("/" + "v1" + "/devices/" + device.getDeviceIdentification() + "/topo/otaReadResponse", "普通设备回复物联网平台读取设备固件版本指令");

            }
            //设备基础Topic数据存储
            for (Map.Entry<String, String> entry : topicMap.entrySet()) {
                DeviceTopic deviceTopic = new DeviceTopic();
                deviceTopic.setDeviceIdentification(device.getDeviceIdentification());
                deviceTopic.setType(DeviceTopicEnum.BASIS.getKey());
                deviceTopic.setTopic(entry.getKey());
                if (entry.getKey().startsWith("/" + "v1" + "/devices/") && entry.getKey().endsWith("datas")) {
                    deviceTopic.setPublisher("边设备");
                    deviceTopic.setSubscriber("物联网平台");
                } else if (entry.getKey().startsWith("/" + "v1" + "/devices/") && entry.getKey().endsWith("commandResponse")) {
                    deviceTopic.setPublisher("边设备");
                    deviceTopic.setSubscriber("物联网平台");
                } else if (entry.getKey().startsWith("/" + "v1" + "/devices/") && (entry.getKey().endsWith("Response") || entry.getKey().endsWith("command"))) {
                    deviceTopic.setPublisher("物联网平台");
                    deviceTopic.setSubscriber("边设备");
                } else {
                    deviceTopic.setPublisher("边设备");
                    deviceTopic.setSubscriber("物联网平台");
                }
                deviceTopic.setRemark(entry.getValue());
                deviceTopic.setCreateBy("admin");
                deviceTopicService.insertSelective(deviceTopic);
            }
        }
        return insertDeviceCount;
    }

    /**
     * 修改设备管理
     *
     * @param deviceParams 设备管理
     * @return 结果
     */
    @Override
    @Transactional(propagation = Propagation.REQUIRES_NEW, rollbackFor = Exception.class)
    public int updateDevice(Device deviceParams) throws Exception {
        Device device = new Device();
        BeanUtils.copyProperties(deviceParams, device);
        device.setUpdateBy("admin");
        final int insertDeviceCount = deviceMapper.insertOrUpdateSelective(device);
        return deviceMapper.updateDevice(device);
    }

    /**
     * 批量删除设备管理
     *
     * @param ids 需要删除的设备管理主键
     * @return 结果
     */
    @Override
    public int deleteDeviceByIds(Long[] ids) {
        return deviceMapper.deleteDeviceByIds(ids);
    }

    /**
     * 删除设备管理信息
     *
     * @param id 设备管理主键
     * @return 结果
     */
    @Override
    public int deleteDeviceById(Long id) {
        return deviceMapper.deleteDeviceById(id);
    }

    @Override
    public Device findOneByClientId(String clientId) {
        return deviceMapper.findOneByClientId(clientId);
    }

    @Override
    public Device findOneByClientIdAndDeviceIdentification(String clientId, String deviceIdentification) {
        return deviceMapper.findOneByClientIdAndDeviceIdentification(clientId, deviceIdentification);
    }

    @Override
    public Device findOneByDeviceIdentification(String deviceIdentification) {
        return deviceMapper.findOneByDeviceIdentification(deviceIdentification);
    }

    @Override
    public Device findOneByClientIdOrderByDeviceIdentification(String clientId) {
        return deviceMapper.findOneByClientIdOrderByDeviceIdentification(clientId);
    }

    @Override
    public Device findOneByClientIdOrDeviceIdentification(String clientId, String deviceIdentification) {
        return deviceMapper.findOneByClientIdOrDeviceIdentification(clientId, deviceIdentification);
    }

    /**
     * 设备信息缓存失效
     *
     * @param clientId
     * @return
     */
    @Override
    public Boolean cacheInvalidation(String clientId) {
        Device oneByClientId = deviceMapper.findOneByClientId(clientId);
        //设备信息缓存失效 删除缓存 更新数据库设备状态
        if (StringUtils.isNotNull(oneByClientId)) {
            //删除缓存
            redisService.delete(CacheConstants.DEF_DEVICE + oneByClientId.getDeviceIdentification());
            //更新数据库设备状态
            Device device = new Device();
            device.setId(oneByClientId.getId());
            device.setConnectStatus(DeviceConnectStatusEnum.OFFLINE.getValue());
            deviceMapper.updateByPrimaryKeySelective(device);
        }
        return true;
    }

    /**
     * 批量断开设备连接端口
     *
     * @param ids
     * @return
     */
    @Override
    public Boolean disconnect(Long[] ids) {
        final List<Device> deviceList = deviceMapper.findAllByIdIn(Arrays.asList(ids));
        if (isEmpty(deviceList)) {
            return false;
        }
        final List<String> clientIdentifiers = deviceList.stream().map(Device::getClientId).collect(Collectors.toList());
        final R r = remoteMqttBrokerOpenApi.closeConnection(clientIdentifiers);
        log.info("主动断开设备ID: {} 连接 , Broker 处理结果: {}", clientIdentifiers, r.toString());
        return r.getCode() == ResultEnum.SUCCESS.getCode();
    }

    @Override
    public Long countDistinctClientIdByConnectStatus(String connectStatus) {
        return deviceMapper.countDistinctClientIdByConnectStatus(connectStatus);
    }

    @Override
    public List<String> selectByProductIdentification(String productIdentification) {
        return deviceMapper.selectByProductIdentification(productIdentification);
    }

    /**
     * 客户端身份认证
     *
     * @param clientIdentifier 客户端
     * @param username         用户名
     * @param password         密码
     * @param deviceStatus     设备状态
     * @param protocolType     协议类型
     * @return
     */
    @Override
    public Device clientAuthentication(String clientIdentifier, String username, String password, String deviceStatus, String protocolType) {
        final Device device = this.findOneByClientIdAndUserNameAndPasswordAndDeviceStatusAndProtocolType(clientIdentifier, username, password, deviceStatus, protocolType);
        if (Optional.ofNullable(device).isPresent()) {
            //缓存设备信息
            redisService.setCacheObject(CacheConstants.DEF_DEVICE + device.getDeviceIdentification(), transformToDeviceCacheVO(device), 30L + Long.parseLong(DateUtils.getRandom(1)), TimeUnit.MILLISECONDS);
            //更改设备在线状态为在线
            this.updateConnectStatusByClientId(DeviceConnectStatusEnum.ONLINE.getValue(), clientIdentifier);
            return device;
        }
        return null;
    }

    @Override
    public List<Device> findAllByIdIn(Collection<Long> idCollection) {
        return deviceMapper.findAllByIdIn(idCollection);
    }

    @Override
    public List<Device> findAllByProductIdentification(String productIdentification) {
        return deviceMapper.findAllByProductIdentification(productIdentification);
    }

    @Override
    public Device selectByProductIdentificationAndDeviceIdentification(String productIdentification, String deviceIdentification) {
        return deviceMapper.selectByProductIdentificationAndDeviceIdentification(productIdentification, deviceIdentification);
    }

    /**
     * 查询设备详细信息
     *
     * @param id
     * @return
     */
    @Override
    public DeviceParams selectDeviceModelById(Long id) {
        DeviceParams deviceParams = new DeviceParams();
        BeanUtils.copyProperties(this.selectDeviceById(id), deviceParams);
        deviceParams.setDeviceLocation(deviceLocationService.findOneByDeviceIdentification(deviceParams.getDeviceIdentification()));
        return deviceParams;
    }


    public List<Device> selectDeviceByDeviceIdentificationList(List<String> deviceIdentificationList) {
        return deviceMapper.selectDeviceByDeviceIdentificationList(deviceIdentificationList);
    }

    /**
     * MQTT协议下上报设备数据
     *
     * @param topoDeviceDataReportParam 上报参数
     * @return {@link TopoDeviceOperationResultVO} 上报结果
     */
    @Override
    public TopoDeviceOperationResultVO deviceDataReportByMqtt(TopoDeviceDataReportParam topoDeviceDataReportParam) {
        return null;
    }

    /**
     * Http协议下上报设备数据
     *
     * @param topoDeviceDataReportParam 上报参数
     * @return {@link TopoDeviceOperationResultVO} 上报结果
     */
    @Override
    public TopoDeviceOperationResultVO deviceDataReportByHttp(TopoDeviceDataReportParam topoDeviceDataReportParam) {
        return null;
    }

    /**
     * Queries device information using the MQTT protocol.
     *
     * @param topoQueryDeviceParam The device query parameters.
     * @return {@link TopoQueryDeviceResultVO} The result of the device query.
     */
    @Override
    public TopoQueryDeviceResultVO queryDeviceByMqtt(TopoQueryDeviceParam topoQueryDeviceParam) {
        return queryDeviceInfo(topoQueryDeviceParam);
    }

    /**
     * Queries device information using the HTTP protocol.
     *
     * @param topoQueryDeviceParam The device query parameters.
     * @return {@link TopoQueryDeviceResultVO} The result of the device query.
     */
    @Override
    public TopoQueryDeviceResultVO queryDeviceByHttp(TopoQueryDeviceParam topoQueryDeviceParam) {
        return queryDeviceInfo(topoQueryDeviceParam);
    }


    /**
     * Queries device information based on provided parameters.
     *
     * @param topoQueryDeviceParam Parameters for querying device information.
     * @return {@link TopoQueryDeviceResultVO} containing the results of the device query.
     */
    private TopoQueryDeviceResultVO queryDeviceInfo(TopoQueryDeviceParam topoQueryDeviceParam) {
        // Create an instance for the result
        TopoQueryDeviceResultVO topoQueryDeviceResultVO = new TopoQueryDeviceResultVO();

        // Create a list to store the results of device information queries
        List<TopoQueryDeviceResultVO.DataItem> deviceInfoList = Optional.ofNullable(topoQueryDeviceParam.getDeviceIds())
                .orElse(Collections.emptyList())
                .stream()
                .distinct()
                .map(deviceIdentification -> {
                    TopoQueryDeviceResultVO.DataItem dataItem = new TopoQueryDeviceResultVO.DataItem();
                    try {
                        dataItem.setDeviceId(deviceIdentification);
                        // Attempt to find device information based on the identification
                        Optional<Device> optionalDevice = Optional.ofNullable(deviceMapper.findOneByDeviceIdentification(deviceIdentification));
                        TopoQueryDeviceResultVO.DataItem.DeviceInfo deviceInfo = optionalDevice
                                .map(device -> BeanUtil.toBean(device, TopoQueryDeviceResultVO.DataItem.DeviceInfo.class))
                                .orElse(new TopoQueryDeviceResultVO.DataItem.DeviceInfo());

                        // Set device information and status based on query result
                        dataItem.setDeviceInfo(deviceInfo)
                                .setStatusCode(optionalDevice.isPresent() ? MqttProtocolTopoStatusEnum.SUCCESS.getValue() : MqttProtocolTopoStatusEnum.FAILURE.getValue())
                                .setStatusDesc(optionalDevice.isPresent() ? MqttProtocolTopoStatusEnum.SUCCESS.getDesc() : "Device not found");
                    } catch (Exception e) {
                        // Handle any exceptions and set the error information in the data item
                        dataItem.setStatusCode(MqttProtocolTopoStatusEnum.FAILURE.getValue())
                                .setStatusDesc("Error querying device: " + e.getMessage());
                    }
                    return dataItem;
                })
                .collect(Collectors.toList());

        // Set the list of device information into the result instance
        topoQueryDeviceResultVO.setData(deviceInfoList)
                .setStatusCode(MqttProtocolTopoStatusEnum.SUCCESS.getValue())
                .setStatusDesc("Query completed");
        return topoQueryDeviceResultVO;
    }

    @Override
    public Long findDeviceTotal() {
        return deviceMapper.findDeviceTotal();
    }

    @Override
    public List<Device> findDevices() {
        return deviceMapper.findDevices();
    }

    private String getCaCertificate() throws IOException {
        //TODO 从数据库获取CA证书 验证
        byte[] bytes = Files.readAllBytes(Paths.get(""));
        return Base64.getEncoder().encodeToString(bytes);
    }

    /**
     * Transforms a device object into a DeviceCacheVO object with associated product data.
     *
     * @param device Device object to be transformed.
     * @return Transformed DeviceCacheVO object.
     */
    private DeviceCacheVO transformToDeviceCacheVO(Device device) {
        DeviceCacheVO deviceCacheVO = BeanUtil.toBeanIgnoreError(device, DeviceCacheVO.class);

        Optional.ofNullable(deviceCacheVO.getProductIdentification())
                .map(productService::findOneByProductIdentification)
                .ifPresent(product -> {
                    ProductCacheVO productCacheVO = BeanPlusUtil.toBeanIgnoreError(product, ProductCacheVO.class);
                    deviceCacheVO.setProductCacheVO(productCacheVO);
                });

        return deviceCacheVO;
    }
}

