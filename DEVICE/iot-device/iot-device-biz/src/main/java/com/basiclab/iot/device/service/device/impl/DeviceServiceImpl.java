package com.basiclab.iot.device.service.device.impl;

import cn.hutool.core.bean.BeanUtil;
import cn.hutool.core.util.StrUtil;
import com.alibaba.excel.EasyExcel;
import com.alibaba.excel.support.ExcelTypeEnum;
import com.alibaba.fastjson2.JSONObject;
import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.conditions.update.LambdaUpdateWrapper;
import com.baomidou.mybatisplus.core.toolkit.Wrappers;
import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.basiclab.iot.common.constant.CacheConstants;
import com.basiclab.iot.common.constant.Constants;
import com.basiclab.iot.common.core.aop.TenantIgnore;
import com.basiclab.iot.common.domain.R;
import com.basiclab.iot.common.service.RedisService;
import com.basiclab.iot.common.utils.DateUtils;
import com.basiclab.iot.common.utils.SnowflakeIdUtil;
import com.basiclab.iot.common.utils.StringUtils;
import com.basiclab.iot.common.utils.bean.BeanPlusUtil;
import com.basiclab.iot.common.utils.tdengine.TdUtils;
import com.basiclab.iot.device.constant.DeviceStatusConstant;
import com.basiclab.iot.device.constant.RedisPrefixConst;
import com.basiclab.iot.device.dal.pgsql.device.DeviceCameraLinkMapper;
import com.basiclab.iot.device.dal.pgsql.device.DeviceMapper;
import com.basiclab.iot.device.domain.device.oo.DeviceReportOo;
import com.basiclab.iot.device.domain.device.qo.DeviceIsExistQo;
import com.basiclab.iot.device.domain.device.vo.*;
import com.basiclab.iot.device.enums.device.DeviceConnectStatusEnum;
import com.basiclab.iot.device.enums.device.DeviceTopicEnum;
import com.basiclab.iot.device.enums.device.DeviceType;
import com.basiclab.iot.device.enums.device.MqttProtocolTopoStatusEnum;
import com.basiclab.iot.device.hooks.BaseHook;
import com.basiclab.iot.device.hooks.ConnectedHook;
import com.basiclab.iot.device.hooks.DisconnectedHook;
import com.basiclab.iot.device.messagebus.ServiceInvokeResponseHandler;
import com.basiclab.iot.device.service.device.DeviceLocationService;
import com.basiclab.iot.device.service.device.DeviceService;
import com.basiclab.iot.device.service.device.DeviceServiceInvokeResponseService;
import com.basiclab.iot.device.service.device.DeviceTopicService;
import com.basiclab.iot.sink.util.IotDeviceMessageUtils;
import com.basiclab.iot.device.service.product.ProductPropertiesService;
import com.basiclab.iot.device.service.product.ProductService;
import com.basiclab.iot.device.service.product.ProductServicesService;
import com.basiclab.iot.file.RemoteFileService;
import com.basiclab.iot.file.domain.vo.SysFileVo;
import com.basiclab.iot.sink.biz.IotDownstreamMessageApi;
import com.basiclab.iot.sink.enums.IotDeviceMessageMethodEnum;
import com.basiclab.iot.sink.enums.IotDeviceTopicEnum;
import com.basiclab.iot.sink.mq.message.IotDeviceMessage;
import com.basiclab.iot.tdengine.RemoteTdEngineService;
import com.basiclab.iot.tdengine.domain.SelectDto;
import lombok.extern.slf4j.Slf4j;
import org.apache.commons.fileupload.FileItem;
import org.apache.commons.fileupload.FileItemFactory;
import org.apache.commons.fileupload.disk.DiskFileItemFactory;
import org.apache.commons.lang3.ObjectUtils;
import org.jetbrains.annotations.NotNull;
import org.springframework.beans.BeanUtils;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Isolation;
import org.springframework.transaction.annotation.Propagation;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.multipart.MultipartFile;
import org.springframework.web.multipart.commons.CommonsMultipartFile;

import javax.annotation.Resource;
import javax.servlet.http.HttpServletResponse;
import java.io.OutputStream;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.*;
import java.util.concurrent.TimeUnit;
import java.util.stream.Collectors;

import static com.basiclab.iot.common.utils.StringUtils.isEmpty;

/**
 * DeviceLocationServiceImpl
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Service
@Slf4j
@Transactional(isolation = Isolation.DEFAULT, propagation = Propagation.REQUIRES_NEW, rollbackFor = Exception.class)
public class DeviceServiceImpl extends ServiceImpl<DeviceMapper, Device> implements DeviceService {

    @Resource
    private DeviceMapper deviceMapper;
    @Resource
    private DeviceCameraLinkMapper deviceCameraLinkMapper;
    @Resource
    private RedisService redisService;
    @Autowired(required = false)
    private IotDownstreamMessageApi iotDownstreamMessageApi;
    @Resource
    private DeviceTopicService deviceTopicService;
    @Resource
    private ProductService productService;
    @Resource
    private DeviceLocationService deviceLocationService;
    @Resource
    private ProductServicesService productServicesService;
    @Resource
    private ProductPropertiesService productPropertiesService;
    @Resource
    private RemoteTdEngineService remoteTdEngineService;
    @Resource
    private RemoteFileService remoteFileService;
    @Resource
    private DeviceServiceInvokeResponseService deviceServiceInvokeResponseService;
    @Value("${spring.datasource.dynamic.datasource.master.dbName:iot}")
    private String dataBaseName;

    @Override
    public Boolean isExist(DeviceIsExistQo deviceIsExistQo) {
        //deviceIdentification和deviceSN有其中一个就判断一个，否则两个同时判断是否存在
        Boolean flag = false;
        if (!isEmpty(deviceIsExistQo.getDeviceIdentification())) {
            LambdaQueryWrapper<Device> wrapper = Wrappers.lambdaQuery();
            wrapper.eq(Device::getDeviceIdentification, deviceIsExistQo.getDeviceIdentification());
            Device device = this.baseMapper.selectOne(wrapper);
            if (!ObjectUtils.isEmpty(device)) {
                flag = true;
            } else {
                flag = false;
            }
        }
        if (!isEmpty(deviceIsExistQo.getDeviceSn())) {
            LambdaQueryWrapper<Device> wrapper = Wrappers.lambdaQuery();
            wrapper.eq(Device::getDeviceSn, deviceIsExistQo.getDeviceSn());
            Device device = this.baseMapper.selectOne(wrapper);
            if (!ObjectUtils.isEmpty(device)) {
                flag = true;
            } else {
                flag = false;
            }
        }
        return flag;
    }

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
    public int batchInsert(DeviceBatchInsertReq req, HttpServletResponse response) {
        Product product = productService.selectByProductIdentification(req.getProductIdentification());
        ArrayList<Device> devices = new ArrayList<>();
        ArrayList<DeviceBatchDetail> deviceBatchDetails = new ArrayList<>();

        //创建设备和批次详情记录，分别存放在devices和deviceBatchDetails
        this.buildDeviceAndBatchDetail(req, product, devices, deviceBatchDetails, null);
        //分批插入设备、批次详情记录并更新批次表
        return insertDeviceAndRecord(req, devices, deviceBatchDetails, response);
    }

    @Override
    public Integer batchImport(DeviceBatchInsertReq req, HttpServletResponse response) {
        Product product = productService.selectByProductIdentification(req.getProductIdentification());
        ArrayList<Device> devices = new ArrayList<>();
        ArrayList<DeviceBatchDetail> deviceBatchDetails = new ArrayList<>();
        List<UploadData> deviceList = redisService.setMembers(RedisPrefixConst.DEVICE_BATCH_IMPORT + req.getFileId())
                .stream()
                .map(item -> JSONObject.parseObject(item, UploadData.class))
                .collect(Collectors.toList());
        //检查输入的sn在数据库中是否存在
        List<String> deviceSnList = deviceList.stream().map(UploadData::getDeviceSn).collect(Collectors.toList());
        List<Device> existDeviceList = deviceMapper.selectByDeviceSnList(deviceSnList);
        List<String> existList = existDeviceList.stream().map(Device::getDeviceSn).collect(Collectors.toList());
        //过滤已存在的设备
        deviceList = deviceList.stream().filter(item -> !existList.contains(item.getDeviceSn())).collect(Collectors.toList());
        //创建设备和批次详情记录，分别存放在devices和deviceBatchDetails
        this.buildDeviceAndBatchDetail(req, product, devices, deviceBatchDetails, deviceList);
        //创建异常批次详情记录
        for (Device device : existDeviceList) {
            DeviceBatchDetail deviceBatchDetail = getDeviceBatchDetail(req, device, DeviceBatchDetail.CreateStatusEnum.FAILURE.getStatus());
            deviceBatchDetails.add(deviceBatchDetail);
        }
        //分批插入设备、批次详情记录并更新批次表
        return insertDeviceAndRecord(req, devices, deviceBatchDetails, response);
    }


    /**
     * DeviceServiceImpl
     *
     * @author 翱翔的雄库鲁
     * @email andywebjava@163.com
     * @wechat EasyAIoT2025
     */

    @Transactional(rollbackFor = Exception.class)
    public int insertDeviceAndRecord(DeviceBatchInsertReq req, ArrayList<Device> devices, ArrayList<DeviceBatchDetail> deviceBatchDetails, HttpServletResponse response) {
        if (devices.isEmpty() && deviceBatchDetails.isEmpty()) {
            return 0;
        }
        return this.insert(devices, deviceBatchDetails);
    }

    private int insert(ArrayList<Device> devices, ArrayList<DeviceBatchDetail> deviceBatchDetails) {
        return deviceMapper.batchInsert(devices);
    }

    private R<SysFileVo> upload(List<DeviceMassProductionVo> deviceMassProductionVos) {
        String fileName = "Equipment_Mass_Production_Information_" + LocalDateTime.now().format(DateTimeFormatter.ofPattern("yyyy-MM-dd_HH-mm-ss")) + ".xlsx";
        FileItemFactory factory = new DiskFileItemFactory(16, null);
        FileItem fileItem = factory.createItem("textField", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", true, fileName);
        MultipartFile multipartFile;
        try {
            OutputStream os = fileItem.getOutputStream();
            EasyExcel.write(os, DeviceMassProductionVo.class)
                    .excelType(ExcelTypeEnum.XLSX)
                    .sheet("info")
                    .doWrite(deviceMassProductionVos);
            os.close();
            //FileItem转MultipartFile
            multipartFile = new CommonsMultipartFile(fileItem);
        } catch (Exception e) {
            e.printStackTrace();
            log.error("文件生成失败");
            throw new RuntimeException(e.getMessage());
        }
        //上传minio
        R<SysFileVo> upload = remoteFileService.upload(multipartFile);
        return upload;
    }

    /**
     * 创建设备和批次详情记录，分别存放在devices和deviceBatchDetails
     *
     * @param req                请求
     * @param product            产品信息
     * @param devices            设备列表
     * @param deviceBatchDetails 设备批次列表
     * @param uploadData         UploadData实体，记录了deviceSn
     */
    private void buildDeviceAndBatchDetail(DeviceBatchInsertReq req, Product product, ArrayList<Device> devices, ArrayList<DeviceBatchDetail> deviceBatchDetails, List<UploadData> uploadData) {
        if (req.getDeviceCount() != null && req.getDeviceCount() != 0) {
            //自动生成
            for (int i = 0; i < req.getDeviceCount(); i++) {
                build(req, product, devices, deviceBatchDetails, null);
            }
        } else if (uploadData != null && !uploadData.isEmpty()) {
            //批量导入
            for (UploadData uploadDatum : uploadData) {
                build(req, product, devices, deviceBatchDetails, uploadDatum);
            }
        } else {
            log.warn("无需要生成的设备记录");
        }

    }

    private void build(DeviceBatchInsertReq req, Product product, ArrayList<Device> devices, ArrayList<DeviceBatchDetail> deviceBatchDetails, UploadData uploadData) {
        String deviceIdentification = SnowflakeIdUtil.nextId();
        String deviceName = product.getProductName() + "-" + deviceIdentification.substring(deviceIdentification.length() - 4);
        String deviceSn;
        if (uploadData != null) {
            deviceSn = uploadData.getDeviceSn();
        } else {
            deviceSn = SnowflakeIdUtil.nextId();
        }
        Device device = getDevice(product, deviceIdentification, deviceName, deviceSn);
        devices.add(device);
        DeviceBatchDetail deviceBatchDetail = getDeviceBatchDetail(req, device, DeviceBatchDetail.CreateStatusEnum.SUCCESS.getStatus());
        deviceBatchDetails.add(deviceBatchDetail);
    }

    @NotNull
    private static Device getDevice(Product product, String deviceIdentification, String deviceName, String deviceSn) {
        Device device = new Device();
        device.setClientId("DEFAULT");
        device.setAppId("DEFAULT");
        device.setDeviceIdentification(deviceIdentification);
        device.setDeviceName(deviceName);
        device.setDeviceStatus("ENABLE");
        device.setConnectStatus("OFFLINE");
        device.setProductIdentification(product.getProductIdentification());
        device.setDeviceSn(deviceSn);
        device.setAppId("默认场景");
        device.setDeviceType(product.getProductType());
        return device;
    }

    @NotNull
    private DeviceBatchDetail getDeviceBatchDetail(DeviceBatchInsertReq req, Device device, Integer createStatus) {
        DeviceBatchDetail deviceBatchDetail = new DeviceBatchDetail();
        deviceBatchDetail.setBatchNumber(req.getBatchNumber());
        deviceBatchDetail.setDeviceName(device.getDeviceName());
        deviceBatchDetail.setDeviceSn(device.getDeviceSn());
        deviceBatchDetail.setDeviceIdentification(device.getDeviceIdentification());
        deviceBatchDetail.setCreateStatus(createStatus);
        if (DeviceBatchDetail.CreateStatusEnum.FAILURE.getStatus().equals(createStatus)) {
            deviceBatchDetail.setFailureCase("添加设备失败，原因：设备sn重复");
        }
        return deviceBatchDetail;
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
    public List<Device> findByAll(Device device) {
        return deviceMapper.findByAll(device);
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
     * @param device 设备管理
     * @return 结果
     */
    @Override
    @Transactional(propagation = Propagation.REQUIRES_NEW, rollbackFor = Exception.class)
    public int insertDevice(Device device) throws Exception {
        Product product = productService.selectByProductIdentification(device.getProductIdentification());
        if (product == null) {
            throw new IllegalArgumentException("产品不存在");
        }
        validateIndustrialPointBindings(device, product);
        device.setConnectStatus(DeviceConnectStatusEnum.OFFLINE.getValue());
        device.setDeviceType(product.getProductType());
        final int insertDeviceCount = deviceMapper.insertOrUpdateSelective(device);

        if (insertDeviceCount > 0) {
            //设备位置信息存储
            /*DeviceLocation deviceLocation = new DeviceLocation();
            BeanUtils.copyProperties(deviceParams.getDeviceLocation(), deviceLocation);
            deviceLocation.setDeviceIdentification(device.getDeviceIdentification());
            deviceLocationService.insertOrUpdateSelective(deviceLocation);*/

            // 基础 TOPIC：与 iot-sink IotDeviceTopicEnum / 前端 Topic 页一致的 /iot/{product}/{device}/... 标准
            String productId = device.getProductIdentification();
            String deviceId = device.getDeviceIdentification();
            for (IotDeviceTopicEnum topicEnum : IotDeviceTopicEnum.values()) {
                String topic = topicEnum.getTopicTemplate().contains("${identifier}")
                        ? topicEnum.buildTopic(productId, deviceId, "{identifier}")
                        : topicEnum.buildTopic(productId, deviceId);
                DeviceTopic deviceTopic = new DeviceTopic();
                deviceTopic.setDeviceIdentification(deviceId);
                deviceTopic.setType(DeviceTopicEnum.BASIS.getKey());
                deviceTopic.setTopic(topic);
                if (topicEnum.isNeedReply()) {
                    deviceTopic.setPublisher("物联网平台");
                    deviceTopic.setSubscriber("设备");
                } else {
                    deviceTopic.setPublisher("设备");
                    deviceTopic.setSubscriber("物联网平台");
                }
                deviceTopic.setRemark(topicEnum.getDescription());
                deviceTopicService.save(deviceTopic);
            }
        }
        return insertDeviceCount;
    }

    /**
     * 修改设备管理
     *
     * @param device 设备管理
     * @return 结果
     */
    @Override
    @Transactional(propagation = Propagation.REQUIRES_NEW, rollbackFor = Exception.class)
    public int updateDevice(Device device) throws Exception {
        Product product = null;
        String productIdentification = device.getProductIdentification();
        if (StrUtil.isBlank(productIdentification) && device.getId() != null) {
            Device existing = findOneById(device.getId());
            if (existing != null) {
                productIdentification = existing.getProductIdentification();
                if (StrUtil.isBlank(device.getExtension())) {
                    device.setExtension(existing.getExtension());
                }
            }
        }
        if (StrUtil.isNotBlank(productIdentification)) {
            product = productService.selectByProductIdentification(productIdentification);
        }
        if (product != null) {
            validateIndustrialPointBindings(device, product);
        }
        return deviceMapper.updateDevice(device);
    }

    private static final Set<String> INDUSTRIAL_PROTOCOLS = Set.of("MODBUS_TCP", "MODBUS_RTU", "OPCUA", "MODBUS");

    /**
     * 工业协议设备：校验点位已绑定物模型属性，且同一设备内绑定唯一。
     * 兼容旧配置：仅有 identifier、无 propertyCode 时，以 identifier 作为绑定键。
     */
    private void validateIndustrialPointBindings(Device device, Product product) {
        if (device == null || product == null || !INDUSTRIAL_PROTOCOLS.contains(
                StrUtil.blankToDefault(product.getProtocolType(), "").toUpperCase())) {
            return;
        }
        if (StrUtil.isBlank(device.getExtension())) {
            throw new IllegalArgumentException("工业协议设备必须配置协议点位（extension.protocolConfig）");
        }
        JSONObject root;
        try {
            root = JSONObject.parseObject(device.getExtension());
        } catch (Exception e) {
            throw new IllegalArgumentException("设备扩展配置 JSON 无效");
        }
        if (root == null) {
            throw new IllegalArgumentException("工业协议设备必须配置协议点位（extension.protocolConfig）");
        }
        JSONObject protocolConfig = root.getJSONObject("protocolConfig");
        if (protocolConfig == null) {
            throw new IllegalArgumentException("工业协议设备缺少 protocolConfig");
        }
        com.alibaba.fastjson2.JSONArray pointsArr = protocolConfig.getJSONArray("points");
        if (pointsArr == null || pointsArr.isEmpty()) {
            throw new IllegalArgumentException("工业协议设备至少配置一个采集点位");
        }
        List<JSONObject> points = new ArrayList<>(pointsArr.size());
        for (int i = 0; i < pointsArr.size(); i++) {
            points.add(pointsArr.getJSONObject(i));
        }

        ProductProperties query = new ProductProperties();
        query.setProductIdentification(product.getProductIdentification());
        List<ProductProperties> properties = productPropertiesService.selectProductPropertiesList(query);
        Set<String> modelCodes = properties == null ? Collections.emptySet()
                : properties.stream()
                .map(ProductProperties::getPropertyCode)
                .filter(StrUtil::isNotBlank)
                .collect(Collectors.toSet());

        Set<String> boundCodes = new LinkedHashSet<>();
        for (int i = 0; i < points.size(); i++) {
            JSONObject point = points.get(i);
            if (point == null) {
                continue;
            }
            String propertyCode = StrUtil.blankToDefault(point.getString("propertyCode"),
                    point.getString("identifier"));
            if (StrUtil.isBlank(propertyCode)) {
                throw new IllegalArgumentException("第 " + (i + 1) + " 个点位未绑定物模型属性");
            }
            if (!modelCodes.isEmpty() && !modelCodes.contains(propertyCode)) {
                throw new IllegalArgumentException("点位绑定的属性「" + propertyCode + "」不存在于产品物模型中");
            }
            if (!boundCodes.add(propertyCode)) {
                throw new IllegalArgumentException("物模型属性「" + propertyCode + "」被多个点位重复绑定");
            }
            Integer decimalPlaces = point.getInteger("decimalPlaces");
            if (decimalPlaces != null && (decimalPlaces < 0 || decimalPlaces > 10)) {
                throw new IllegalArgumentException("第 " + (i + 1) + " 个点位的显示小数位必须在 0 到 10 之间");
            }
            // 回写规范化：保证持久化含 propertyCode，identifier 缺省时等于 propertyCode
            point.put("propertyCode", propertyCode);
            if (StrUtil.isBlank(point.getString("identifier"))) {
                point.put("identifier", propertyCode);
            }
        }
        protocolConfig.put("points", points);
        root.put("protocolConfig", protocolConfig);
        device.setExtension(root.toJSONString());
    }

    @Override
    public void updateDeviceBySys(Device device) {
        deviceMapper.updateDeviceBySys(device);
    }

    /**
     * 批量删除设备管理
     *
     * @param ids 需要删除的设备管理主键
     * @return 结果
     */
    @Override
    public int deleteDeviceByIds(Long[] ids) {
        if (ids != null && ids.length > 0) {
            // 级联清理摄像头关联，避免设备删除后摄像头仍被判定为「已绑定」而无法再次关联
            deviceCameraLinkMapper.deleteByIotDeviceIds(ids);
        }
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
        if (id != null) {
            deviceCameraLinkMapper.deleteByIotDeviceIds(new Long[]{id});
        }
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

    @TenantIgnore
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
            this.updateById(device);
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
        // 使用 iot-sink-api 实现断开连接功能
        final List<String> clientIdentifiers = deviceList.stream().map(Device::getClientId).collect(Collectors.toList());

        try {
            if (iotDownstreamMessageApi != null) {
                int closedCount = iotDownstreamMessageApi.closeConnection(clientIdentifiers);
                log.info("主动断开设备连接，客户端 ID: {}，成功关闭: {}", clientIdentifiers, closedCount);
                return closedCount > 0;
            } else {
                log.warn("IotDownstreamMessageApi 不存在，无法断开连接");
                return false;
            }
        } catch (Exception e) {
            log.error("断开设备连接失败，客户端 ID: {}，错误: {}", clientIdentifiers, e.getMessage(), e);
            return false;
        }
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

    /**
     * 查询普通设备影子数据
     *
     * @param ids       需要查询的普通设备id
     * @param startTime 开始时间 格式：yyyy-MM-dd HH:mm:ss
     * @param endTime   结束时间 格式：yyyy-MM-dd HH:mm:ss
     * @return 普通设备影子数据
     */
    @Override
    public Map<String, List<Map<String, Object>>> getDeviceShadow(String ids, String startTime, String endTime) {
        List<Long> idCollection = Arrays.stream(ids.split(",")).mapToLong(Long::parseLong).boxed().collect(Collectors.toList());
        List<Device> devices = deviceMapper.findAllByIdInAndStatus(idCollection, "ENABLE");
        if (StringUtils.isNull(devices)) {
            log.error("查询普通设备影子数据失败，普通设备不存在");
            return null;
        }
        Map<String, List<Map<String, Object>>> map = new HashMap<>();
        devices.forEach(device -> {
            Product product = productService.selectByProductIdentification(device.getProductIdentification());
            if (StringUtils.isNull(product)) {
                log.error("查询普通设备影子数据失败，设备对应的产品不存在");
                return;
            }
            List<ProductServices> productServicesLis = productServicesService.findAllByProductIdentificationIdAndStatus(product.getProductIdentification(), Constants.ENABLE);
            if (StringUtils.isNull(productServicesLis)) {
                log.error("查询普通设备影子数据失败，普通设备services不存在");
                return;
            }
            productServicesLis.forEach(productServices -> {
                String superTableName = TdUtils.getSuperTableName(product.getProductType(), product.getProductIdentification(), productServices.getServiceCode());
                String shadowTableName = TdUtils.getSubTableName(superTableName, device.getDeviceIdentification());
                SelectDto selectDto = new SelectDto();
                selectDto.setDataBaseName(dataBaseName);
                selectDto.setTableName(shadowTableName);
                if (StringUtils.isNotEmpty(startTime) && StringUtils.isNotEmpty(endTime)) {
                    selectDto.setFieldName("ts");
                    selectDto.setStartTime(DateUtils.localDateTime2Millis(DateUtils.dateToLocalDateTime(DateUtils.strToDate(startTime))));
                    selectDto.setEndTime(DateUtils.localDateTime2Millis(DateUtils.dateToLocalDateTime(DateUtils.strToDate(endTime))));
                    R<?> dataByTimestamp = remoteTdEngineService.getDataByTimestamp(selectDto);
                    if (StringUtils.isNull(dataByTimestamp)) {
                        log.error("查询普通设备影子数据失败，普通设备影子数据不存在");
                    } else {
                        map.put(shadowTableName, (List<Map<String, Object>>) dataByTimestamp.getData());
                        log.info("查询普通设备影子数据成功，普通设备影子数据：{}", dataByTimestamp.getData());

                    }
                } else {
                    R<?> lastData = remoteTdEngineService.getLastData(selectDto);
                    if (StringUtils.isNull(lastData)) {
                        log.error("查询普通设备影子数据失败，普通设备影子数据不存在");
                    } else {
                        map.put(shadowTableName, (List<Map<String, Object>>) lastData.getData());
                        log.info("查询普通设备影子数据成功，普通设备影子数据：{}", lastData.getData());

                    }
                }

            });
        });
        return map;
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

    @Override
    public void report(DeviceReportOo deviceReportOo) {
        //todo  设置需要手动设置的属性
        String deviceIdentification = deviceReportOo.getDeviceIdentification();
        Device device = findOneByDeviceIdentification(deviceIdentification);
        if (Objects.isNull(device)) {
            //只有第一次需要处理的属性
            device = new Device();
            device.setActiveStatus(1);
            device.setActivatedTime(LocalDateTime.now());
        }
        BeanUtils.copyProperties(deviceReportOo, device);
        device.setConnectStatus("ONLINE");
        device.setUpdateTime(LocalDateTime.now());
        device.setLastOnlineTime(LocalDateTime.now());
        saveOrUpdate(device);
    }


    @Override
    public void handleSubscribe(Map<String, Object> params) {

    }

    @Override
    public int associateGateway(List<Long> idList, String targetDeviceIdentification) {
        if (idList == null || idList.isEmpty() || StringUtils.isEmpty(targetDeviceIdentification)) {
            throw new RuntimeException("关联参数不能为空");
        }
        Device gateway = deviceMapper.findOneByDeviceIdentification(targetDeviceIdentification);
        if (gateway == null || !Device.deviceTypeEnum.GATEWAY.getType().equals(gateway.getDeviceType())) {
            throw new RuntimeException("目标关联设备非网关设备");
        }
        int successCount = 0;
        for (Long id : idList) {
            Device subDevice = deviceMapper.selectDeviceById(id);
            if (subDevice == null) {
                throw new RuntimeException("子设备不存在: " + id);
            }
            if (!Device.deviceTypeEnum.SUBSET.getType().equals(subDevice.getDeviceType())) {
                throw new RuntimeException("仅支持关联网关子设备: " + subDevice.getDeviceName());
            }
            if (StringUtils.isNotEmpty(subDevice.getParentIdentification())
                    && !targetDeviceIdentification.equals(subDevice.getParentIdentification())) {
                throw new RuntimeException("子设备已关联其他网关: " + subDevice.getDeviceName());
            }
            LambdaUpdateWrapper<Device> wrapper = Wrappers.lambdaUpdate();
            wrapper.eq(Device::getId, id)
                    .set(Device::getParentIdentification, targetDeviceIdentification)
                    .set(Device::getUpdateTime, LocalDateTime.now());
            if (super.update(wrapper)) {
                successCount++;
            }
        }
        return successCount;
    }

    @Override
    public int disassociateGateway(List<Long> idList) {
        if (idList == null || idList.isEmpty()) {
            throw new RuntimeException("解绑设备列表不能为空");
        }
        int successCount = 0;
        for (Long id : idList) {
            Device subDevice = deviceMapper.selectDeviceById(id);
            if (subDevice == null) {
                continue;
            }
            LambdaUpdateWrapper<Device> wrapper = Wrappers.lambdaUpdate();
            wrapper.eq(Device::getId, id)
                    .set(Device::getParentIdentification, null)
                    .set(Device::getUpdateTime, LocalDateTime.now());
            if (super.update(wrapper)) {
                successCount++;
            }
        }
        return successCount;
    }

    @Override
    public ConnectStatusStatisticsVo getConnectStatusStatistics() {
        return deviceMapper.getConnectStatusStatistics();
    }

    @Override
    public DeviceStatisticsVo getDeviceStatistics() {
        DeviceStatisticsVo deviceStatistics = deviceMapper.getDeviceStatistics();
        deviceStatistics.setDeviceTotal(deviceStatistics.getCommonDeviceAmount() + deviceStatistics.getGatewayDeviceAmount() + deviceStatistics.getSubsetDeviceAmount());
        return deviceStatistics;
    }

    @Override
    public DeviceStatusStatisticsVo getDeviceStatusStatistics() {
        return deviceMapper.getDeviceStatusStatistics();
    }


    @Override
    public void handleConnected(Map<String, Object> params) {
        ConnectedHook model = new ConnectedHook(params);
        String clientId = model.getClientId();
        if (clientId.startsWith(DeviceStatusConstant.DEVICE_CLIENT_HEAD)) {
            log.info("EMQX客户端认证完成并成功接入系统, params=" + JSONObject.toJSONString(model));
            handleConnection(model, DeviceConnectStatusEnum.ONLINE.getValue());
        }
    }

    @Override
    public void handleDisConnected(Map<String, Object> params) {
        DisconnectedHook model = new DisconnectedHook(params);
        String clientId = model.getClientId();
        if (clientId.startsWith(DeviceStatusConstant.DEVICE_CLIENT_HEAD)) {
            log.info("EMQX客户端连接层在准备关闭, params=" + JSONObject.toJSONString(model));
            handleConnection(model, DeviceConnectStatusEnum.OFFLINE.getValue());
        }
    }


    /**
     * 调用消息中心公共逻辑处理
     *
     * @param hook
     * @param status 是否在线
     * @return
     */
    private boolean handleConnection(BaseHook hook, String status) {
        String deviceIdentification = hook.getClientId().substring(7);
        updateDeviceStatus(deviceIdentification, status);
        return true;
    }

    /**
     * 更新设备对应状态
     *
     * @param deviceIdentification 设备标识
     * @param status               是否上线状态
     */
    private void updateDeviceStatus(String deviceIdentification, String status) {
        LambdaUpdateWrapper<Device> wrapper = Wrappers.lambdaUpdate();
        wrapper.eq(Device::getDeviceIdentification, deviceIdentification);
        wrapper.set(Device::getConnectStatus, status);
        if (DeviceConnectStatusEnum.OFFLINE.getValue().equals(status)) {
            wrapper.set(Device::getLastOnlineTime, LocalDateTime.now());
        }
        if (DeviceConnectStatusEnum.ONLINE.getValue().equals(status)) {
            wrapper.set(Device::getLastOnlineTime, LocalDateTime.now());
        }
        super.update(wrapper);
    }

    @Override
    public DeviceExtensionDataVO queryDeviceExtensionData(DeviceExtensionQueryRequest request) {
        try {
            // 查询设备信息
            Device device = this.selectDeviceById(request.getDeviceId());
            if (device == null) {
                log.warn("查询设备扩展信息失败，设备不存在：deviceId={}", request.getDeviceId());
                return null;
            }

            // 构建响应对象
            DeviceExtensionDataVO result = new DeviceExtensionDataVO();
            result.setDeviceId(device.getId());
            result.setDeviceIdentification(device.getDeviceIdentification());
            result.setExtensionType(request.getExtensionType());
            result.setUpdateTime(device.getUpdateTime());

            // 解析 extension 字段
            String extension = device.getExtension();
            if (StringUtils.isEmpty(extension)) {
                log.debug("设备扩展信息为空：deviceId={}", request.getDeviceId());
                result.setExtensionData(null);
                return result;
            }

            try {
                // 解析 JSON
                JSONObject extensionJson = JSONObject.parseObject(extension);

                // 根据扩展信息类型获取对应的数据
                Object extensionData = extensionJson.get(request.getExtensionType());
                result.setExtensionData(extensionData);

                log.debug("查询设备扩展信息成功：deviceId={}, extensionType={}",
                        request.getDeviceId(), request.getExtensionType());
            } catch (Exception e) {
                log.error("解析设备扩展信息失败：deviceId={}, extensionType={}, error={}",
                        request.getDeviceId(), request.getExtensionType(), e.getMessage(), e);
                result.setExtensionData(null);
            }

            return result;
        } catch (Exception e) {
            log.error("查询设备扩展信息异常：deviceId={}, extensionType={}, error={}",
                    request.getDeviceId(), request.getExtensionType(), e.getMessage(), e);
            return null;
        }
    }

    /** 属性期望下发在指令日志中的标识 */
    public static final String PROPERTY_SET_SERVICE_ID = "$property.set";

    @Override
    public Map<String, Object> invokeService(Long deviceId, String serviceIdentifier, Object params) {
        try {
            if (deviceId == null) {
                throw new IllegalArgumentException("设备ID不能为空");
            }
            if (StrUtil.isBlank(serviceIdentifier)) {
                throw new IllegalArgumentException("服务标识不能为空");
            }

            Device device = findOneById(deviceId);
            if (device == null) {
                throw new IllegalArgumentException("设备不存在");
            }

            if (iotDownstreamMessageApi == null) {
                log.warn("[invokeService][IotDownstreamMessageApi 不存在，无法发送服务调用消息，设备ID: {}]", deviceId);
                return null;
            }

            Object normalizedParams = params != null ? params : Collections.emptyMap();
            String productIdentification = device.getProductIdentification();
            String deviceIdentification = device.getDeviceIdentification();
            Device gateway = resolveGatewayForSubset(device);
            String topic;
            Object downlinkParams = normalizedParams;
            if (gateway != null) {
                topic = String.format("/iot/%s/%s/sub/service/downstream/invoke/%s",
                        gateway.getProductIdentification(), gateway.getDeviceIdentification(),
                        serviceIdentifier);
                downlinkParams = wrapSubDeviceDownlinkParams(device, normalizedParams);
            } else {
                topic = String.format("/iot/%s/%s/service/downstream/invoke/%s",
                        productIdentification, deviceIdentification, serviceIdentifier);
            }

            String requestId = IotDeviceMessageUtils.generateMessageId();
            IotDeviceMessage deviceMessage = IotDeviceMessage.requestOf(
                    requestId,
                    IotDeviceMessageMethodEnum.SERVICE_INVOKE.getMethod(),
                    downlinkParams);
            // 下行消息 deviceId 仍指向目标子设备，便于回执关联；Topic 指向网关代理路径
            deviceMessage.setDeviceId(String.valueOf(deviceId));
            deviceMessage.setTenantId(device.getTenantId());
            deviceMessage.setTopic(topic);

            String inputJson = JSONObject.toJSONString(normalizedParams);
            DeviceServiceInvokeResponse pending = DeviceServiceInvokeResponse.builder()
                    .messageId(deviceMessage.getId())
                    .deviceId(deviceId)
                    .deviceIdentification(deviceIdentification)
                    .productIdentification(productIdentification)
                    .serviceIdentifier(serviceIdentifier)
                    .requestId(requestId)
                    .method(deviceMessage.getMethod())
                    .responseData(inputJson)
                    .responseCode(ServiceInvokeResponseHandler.PENDING_CODE)
                    .responseMsg("PENDING")
                    .topic(topic)
                    .reportTime(LocalDateTime.now())
                    .tenantId(device.getTenantId() != null ? device.getTenantId() : 0L)
                    .createTime(LocalDateTime.now())
                    .build();
            deviceServiceInvokeResponseService.save(pending);

            iotDownstreamMessageApi.sendDownstreamMessageByDeviceId(deviceId, deviceMessage);

            log.info("[invokeService][服务调用消息发送成功，设备ID: {}, 服务标识: {}, Topic: {}, requestId: {}]",
                    deviceId, serviceIdentifier, topic, requestId);
            return buildDownlinkResult(requestId, device, topic, serviceIdentifier, normalizedParams);

        } catch (IllegalArgumentException e) {
            throw e;
        } catch (Exception e) {
            log.error("[invokeService][调用设备服务失败，设备ID: {}, 服务标识: {}, 错误: {}]",
                    deviceId, serviceIdentifier, e.getMessage(), e);
            return null;
        }
    }

    @Override
    public Map<String, Object> setProperties(Long deviceId, Object params) {
        try {
            if (deviceId == null) {
                throw new IllegalArgumentException("设备ID不能为空");
            }
            if (!(params instanceof Map) || ((Map<?, ?>) params).isEmpty()) {
                throw new IllegalArgumentException("请至少下发一个属性");
            }
            Device device = findOneById(deviceId);
            if (device == null) {
                throw new IllegalArgumentException("设备不存在");
            }
            if (iotDownstreamMessageApi == null) {
                log.warn("[setProperties][IotDownstreamMessageApi 不存在，设备ID: {}]", deviceId);
                return null;
            }

            @SuppressWarnings("unchecked")
            Map<String, Object> rawProps = (Map<String, Object>) params;
            Map<String, Object> coerced = validateAndCoerceProperties(
                    device.getProductIdentification(), rawProps);

            String productIdentification = device.getProductIdentification();
            String deviceIdentification = device.getDeviceIdentification();
            Device gateway = resolveGatewayForSubset(device);
            String topic;
            Object downlinkParams = coerced;
            if (gateway != null) {
                topic = String.format("/iot/%s/%s/sub/property/downstream/desired/set",
                        gateway.getProductIdentification(), gateway.getDeviceIdentification());
                downlinkParams = wrapSubDeviceDownlinkParams(device, coerced);
            } else {
                topic = String.format("/iot/%s/%s/property/downstream/desired/set",
                        productIdentification, deviceIdentification);
            }

            String requestId = IotDeviceMessageUtils.generateMessageId();
            IotDeviceMessage deviceMessage = IotDeviceMessage.requestOf(
                    requestId,
                    IotDeviceMessageMethodEnum.PROPERTY_SET.getMethod(),
                    downlinkParams);
            deviceMessage.setDeviceId(String.valueOf(deviceId));
            deviceMessage.setTenantId(device.getTenantId());
            deviceMessage.setTopic(topic);

            // 写入云端 desired，便于影子对比与离线期望可见
            mergeDesiredIntoExtension(device, coerced);

            String inputJson = JSONObject.toJSONString(coerced);
            DeviceServiceInvokeResponse pending = DeviceServiceInvokeResponse.builder()
                    .messageId(deviceMessage.getId())
                    .deviceId(deviceId)
                    .deviceIdentification(deviceIdentification)
                    .productIdentification(productIdentification)
                    .serviceIdentifier(PROPERTY_SET_SERVICE_ID)
                    .requestId(requestId)
                    .method(deviceMessage.getMethod())
                    .responseData(inputJson)
                    .responseCode(ServiceInvokeResponseHandler.PENDING_CODE)
                    .responseMsg("PENDING")
                    .topic(topic)
                    .reportTime(LocalDateTime.now())
                    .tenantId(device.getTenantId() != null ? device.getTenantId() : 0L)
                    .createTime(LocalDateTime.now())
                    .build();
            deviceServiceInvokeResponseService.save(pending);

            iotDownstreamMessageApi.sendDownstreamMessageByDeviceId(deviceId, deviceMessage);
            log.info("[setProperties][属性期望值下发成功，设备ID: {}, Topic: {}, requestId: {}]",
                    deviceId, topic, requestId);
            return buildDownlinkResult(requestId, device, topic, PROPERTY_SET_SERVICE_ID, coerced);
        } catch (IllegalArgumentException e) {
            throw e;
        } catch (Exception e) {
            log.error("[setProperties][属性下发失败，设备ID: {}, 错误: {}]",
                    deviceId, e.getMessage(), e);
            return null;
        }
    }

    private Map<String, Object> buildDownlinkResult(String requestId, Device device,
                                                    String topic, String identifier, Object payload) {
        Map<String, Object> result = new LinkedHashMap<>();
        result.put("requestId", requestId);
        result.put("topic", topic);
        result.put("identifier", identifier);
        boolean viaGateway = topic != null && topic.contains("/sub/");
        result.put("viaGateway", viaGateway);
        String effectiveStatus = device.getConnectStatus();
        if (viaGateway && StrUtil.isNotBlank(device.getParentIdentification())) {
            result.put("gatewayIdentification", device.getParentIdentification());
            Device gateway = deviceMapper.findOneByDeviceIdentification(device.getParentIdentification());
            if (gateway != null) {
                effectiveStatus = gateway.getConnectStatus();
                result.put("gatewayConnectStatus", gateway.getConnectStatus());
            }
        }
        result.put("connectStatus", effectiveStatus);
        result.put("offline", !DeviceConnectStatusEnum.ONLINE.getValue()
                .equalsIgnoreCase(String.valueOf(effectiveStatus)));
        result.put("payload", payload);
        return result;
    }

    /**
     * 子设备且已绑定网关时返回网关设备，否则 null（走直连 Topic）
     */
    private Device resolveGatewayForSubset(Device device) {
        if (device == null || !Device.deviceTypeEnum.SUBSET.getType().equals(device.getDeviceType())) {
            return null;
        }
        if (StrUtil.isBlank(device.getParentIdentification())) {
            log.warn("[resolveGatewayForSubset][子设备未关联网关，将按直连 Topic 下发，deviceId={}]",
                    device.getId());
            return null;
        }
        Device gateway = deviceMapper.findOneByDeviceIdentification(device.getParentIdentification());
        if (gateway == null || !Device.deviceTypeEnum.GATEWAY.getType().equals(gateway.getDeviceType())) {
            log.warn("[resolveGatewayForSubset][父设备不是网关或不存在，parent={}]",
                    device.getParentIdentification());
            return null;
        }
        return gateway;
    }

    private Map<String, Object> wrapSubDeviceDownlinkParams(Device subDevice, Object input) {
        Map<String, Object> wrapped = new LinkedHashMap<>();
        wrapped.put("productIdentification", subDevice.getProductIdentification());
        wrapped.put("deviceIdentification", subDevice.getDeviceIdentification());
        wrapped.put("input", input != null ? input : Collections.emptyMap());
        return wrapped;
    }

    @Override
    public Device ensureGatewaySubDevice(EnsureGatewaySubDeviceParam param) {
        if (param == null || StrUtil.hasBlank(param.getGatewayIdentification(),
                param.getProductIdentification(), param.getDeviceIdentification())) {
            throw new IllegalArgumentException("网关/子设备产品/子设备标识不能为空");
        }
        Device gateway = deviceMapper.findOneByDeviceIdentification(param.getGatewayIdentification());
        if (gateway == null || !Device.deviceTypeEnum.GATEWAY.getType().equals(gateway.getDeviceType())) {
            throw new IllegalArgumentException("网关设备不存在或类型不是 GATEWAY: "
                    + param.getGatewayIdentification());
        }
        Product product = productService.selectByProductIdentification(param.getProductIdentification());
        if (product == null) {
            throw new IllegalArgumentException("子设备产品不存在: " + param.getProductIdentification());
        }
        if (!Device.deviceTypeEnum.SUBSET.getType().equals(product.getProductType())
                && !"SUBSET".equalsIgnoreCase(product.getProductType())) {
            throw new IllegalArgumentException("子设备产品类型必须为 SUBSET: "
                    + param.getProductIdentification());
        }

        Device existing = deviceMapper.selectByProductIdentificationAndDeviceIdentification(
                param.getProductIdentification(), param.getDeviceIdentification());
        if (existing != null) {
            if (!Device.deviceTypeEnum.SUBSET.getType().equals(existing.getDeviceType())) {
                throw new IllegalArgumentException("设备已存在但不是子设备类型: "
                        + param.getDeviceIdentification());
            }
            if (StrUtil.isNotBlank(existing.getParentIdentification())
                    && !param.getGatewayIdentification().equals(existing.getParentIdentification())) {
                throw new IllegalArgumentException("子设备已关联其他网关: "
                        + existing.getParentIdentification());
            }
            if (StrUtil.isBlank(existing.getParentIdentification())) {
                LambdaUpdateWrapper<Device> wrapper = Wrappers.lambdaUpdate();
                wrapper.eq(Device::getId, existing.getId())
                        .set(Device::getParentIdentification, param.getGatewayIdentification())
                        .set(Device::getUpdateTime, LocalDateTime.now());
                super.update(wrapper);
                existing.setParentIdentification(param.getGatewayIdentification());
            }
            if (param.getTenantId() != null && existing.getTenantId() == null) {
                existing.setTenantId(param.getTenantId());
            }
            return existing;
        }

        Device created = new Device();
        created.setClientId("gw-sub-" + param.getDeviceIdentification());
        created.setAppId(StrUtil.blankToDefault(gateway.getAppId(), "DEFAULT"));
        created.setDeviceIdentification(param.getDeviceIdentification());
        String name = StrUtil.blankToDefault(param.getDeviceName(),
                product.getProductName() + "-" + param.getDeviceIdentification());
        created.setDeviceName(name);
        created.setDeviceStatus("ENABLE");
        created.setConnectStatus(DeviceConnectStatusEnum.OFFLINE.getValue());
        created.setProductIdentification(param.getProductIdentification());
        created.setDeviceType(Device.deviceTypeEnum.SUBSET.getType());
        created.setParentIdentification(param.getGatewayIdentification());
        created.setTenantId(param.getTenantId() != null ? param.getTenantId() : gateway.getTenantId());
        created.setDeviceSn(param.getDeviceIdentification());
        try {
            insertDevice(created);
        } catch (Exception e) {
            throw new IllegalArgumentException("自动创建子设备失败: " + e.getMessage(), e);
        }
        Device saved = deviceMapper.selectByProductIdentificationAndDeviceIdentification(
                param.getProductIdentification(), param.getDeviceIdentification());
        if (saved == null) {
            throw new IllegalArgumentException("自动创建子设备后查询失败: "
                    + param.getDeviceIdentification());
        }
        // insertOrUpdateSelective 可能未写入 parent/tenant，创建后强制补齐绑定
        LambdaUpdateWrapper<Device> bind = Wrappers.lambdaUpdate();
        bind.eq(Device::getId, saved.getId())
                .set(Device::getParentIdentification, param.getGatewayIdentification())
                .set(Device::getDeviceType, Device.deviceTypeEnum.SUBSET.getType())
                .set(Device::getUpdateTime, LocalDateTime.now());
        if (created.getTenantId() != null) {
            bind.set(Device::getTenantId, created.getTenantId());
        }
        super.update(bind);
        saved.setParentIdentification(param.getGatewayIdentification());
        saved.setDeviceType(Device.deviceTypeEnum.SUBSET.getType());
        if (created.getTenantId() != null) {
            saved.setTenantId(created.getTenantId());
        }
        log.info("[ensureGatewaySubDevice][自动创建子设备成功 gateway={} product={} device={} id={}]",
                param.getGatewayIdentification(), param.getProductIdentification(),
                param.getDeviceIdentification(), saved.getId());
        return saved;
    }

    @Override
    public int detachGatewaySubDevices(String gatewayIdentification, List<String> subDeviceIdentifications) {
        if (StrUtil.isBlank(gatewayIdentification) || subDeviceIdentifications == null
                || subDeviceIdentifications.isEmpty()) {
            return 0;
        }
        int count = 0;
        for (String subId : subDeviceIdentifications) {
            if (StrUtil.isBlank(subId)) {
                continue;
            }
            Device sub = deviceMapper.findOneByDeviceIdentification(subId);
            if (sub == null || !gatewayIdentification.equals(sub.getParentIdentification())) {
                continue;
            }
            LambdaUpdateWrapper<Device> wrapper = Wrappers.lambdaUpdate();
            wrapper.eq(Device::getId, sub.getId())
                    .set(Device::getParentIdentification, null)
                    .set(Device::getConnectStatus, DeviceConnectStatusEnum.OFFLINE.getValue())
                    .set(Device::getUpdateTime, LocalDateTime.now());
            if (super.update(wrapper)) {
                count++;
            }
        }
        return count;
    }

    @Override
    public int updateGatewaySubDeviceStatus(String gatewayIdentification,
                                             List<Map<String, Object>> statusItems) {
        if (StrUtil.isBlank(gatewayIdentification) || statusItems == null || statusItems.isEmpty()) {
            return 0;
        }
        int count = 0;
        for (Map<String, Object> item : statusItems) {
            if (item == null) {
                continue;
            }
            Object idObj = item.get("deviceIdentification");
            if (idObj == null) {
                idObj = item.get("deviceId");
            }
            Object statusObj = item.get("status");
            if (statusObj == null) {
                statusObj = item.get("connectStatus");
            }
            if (idObj == null || statusObj == null) {
                continue;
            }
            String subId = String.valueOf(idObj);
            String status = String.valueOf(statusObj).toUpperCase(Locale.ROOT);
            if (!"ONLINE".equals(status) && !"OFFLINE".equals(status)) {
                continue;
            }
            Device sub = deviceMapper.findOneByDeviceIdentification(subId);
            if (sub == null || !gatewayIdentification.equals(sub.getParentIdentification())) {
                continue;
            }
            LambdaUpdateWrapper<Device> wrapper = Wrappers.lambdaUpdate();
            wrapper.eq(Device::getId, sub.getId())
                    .set(Device::getConnectStatus, status)
                    .set(Device::getUpdateTime, LocalDateTime.now());
            if ("ONLINE".equals(status)) {
                wrapper.set(Device::getLastOnlineTime, LocalDateTime.now())
                        .set(Device::getActiveStatus, 1);
            }
            if (super.update(wrapper)) {
                count++;
            }
        }
        return count;
    }

    @Override
    public Device ensureDeviceOnUplink(EnsureDeviceOnUplinkParam param) {
        if (param == null || StrUtil.hasBlank(param.getProductIdentification(),
                param.getDeviceIdentification())) {
            throw new IllegalArgumentException("产品标识与设备标识不能为空");
        }
        Product product = productService.selectByProductIdentification(param.getProductIdentification());
        if (product == null) {
            throw new IllegalArgumentException("产品不存在: " + param.getProductIdentification());
        }
        String productType = StrUtil.blankToDefault(product.getProductType(), "").toUpperCase(Locale.ROOT);
        // 子设备必须经网关代理建档；此处仅允许网关/普通直连产品
        if (Device.deviceTypeEnum.SUBSET.getType().equals(productType)) {
            throw new IllegalArgumentException("SUBSET 子设备请经网关代理 Topic 自动创建，不能直连建档: "
                    + param.getProductIdentification());
        }
        if (!Device.deviceTypeEnum.GATEWAY.getType().equals(productType)
                && !Device.deviceTypeEnum.COMMON.getType().equals(productType)
                && !Device.deviceTypeEnum.VIDEO_COMMON.getType().equals(productType)) {
            throw new IllegalArgumentException("不支持的产品类型自动建档: " + productType);
        }

        Device existing = deviceMapper.selectByProductIdentificationAndDeviceIdentification(
                param.getProductIdentification(), param.getDeviceIdentification());
        if (existing != null) {
            if (param.getTenantId() != null && existing.getTenantId() == null) {
                LambdaUpdateWrapper<Device> wrapper = Wrappers.lambdaUpdate();
                wrapper.eq(Device::getId, existing.getId())
                        .set(Device::getTenantId, param.getTenantId())
                        .set(Device::getUpdateTime, LocalDateTime.now());
                super.update(wrapper);
                existing.setTenantId(param.getTenantId());
            }
            return existing;
        }

        Device created = new Device();
        String clientId = StrUtil.blankToDefault(param.getClientId(),
                "auto-" + param.getDeviceIdentification());
        created.setClientId(clientId);
        created.setAppId(StrUtil.blankToDefault(product.getAppId(), "DEFAULT"));
        created.setDeviceIdentification(param.getDeviceIdentification());
        String name = StrUtil.blankToDefault(param.getDeviceName(),
                product.getProductName() + "-" + param.getDeviceIdentification());
        created.setDeviceName(name);
        created.setDeviceStatus("ENABLE");
        created.setConnectStatus(DeviceConnectStatusEnum.OFFLINE.getValue());
        created.setProductIdentification(param.getProductIdentification());
        created.setDeviceType(productType);
        created.setTenantId(param.getTenantId());
        created.setDeviceSn(param.getDeviceIdentification());
        try {
            insertDevice(created);
        } catch (Exception e) {
            throw new IllegalArgumentException("上行自动创建设备失败: " + e.getMessage(), e);
        }
        Device saved = deviceMapper.selectByProductIdentificationAndDeviceIdentification(
                param.getProductIdentification(), param.getDeviceIdentification());
        if (saved == null) {
            throw new IllegalArgumentException("上行自动创建设备后查询失败: "
                    + param.getDeviceIdentification());
        }
        if (param.getTenantId() != null
                && (saved.getTenantId() == null || !param.getTenantId().equals(saved.getTenantId()))) {
            LambdaUpdateWrapper<Device> bind = Wrappers.lambdaUpdate();
            bind.eq(Device::getId, saved.getId())
                    .set(Device::getTenantId, param.getTenantId())
                    .set(Device::getDeviceType, productType)
                    .set(Device::getUpdateTime, LocalDateTime.now());
            super.update(bind);
            saved.setTenantId(param.getTenantId());
            saved.setDeviceType(productType);
        }
        log.info("[ensureDeviceOnUplink][自动创建设备成功 product={} device={} type={} id={}]",
                param.getProductIdentification(), param.getDeviceIdentification(),
                productType, saved.getId());
        return saved;
    }

    /**
     * 按物模型校验可写属性并做类型强制转换
     */
    private Map<String, Object> validateAndCoerceProperties(String productIdentification,
                                                            Map<String, Object> rawProps) {
        if (StrUtil.isBlank(productIdentification)) {
            // 无产品标识时透传，但仍做基础类型整理
            Map<String, Object> passthrough = new LinkedHashMap<>();
            rawProps.forEach((k, v) -> {
                if (StrUtil.isNotBlank(k) && v != null) {
                    passthrough.put(k, v);
                }
            });
            if (passthrough.isEmpty()) {
                throw new IllegalArgumentException("请至少下发一个属性");
            }
            return passthrough;
        }

        ProductProperties query = new ProductProperties();
        query.setProductIdentification(productIdentification);
        List<ProductProperties> allProps = productPropertiesService.selectProductPropertiesList(query);
        Map<String, ProductProperties> byCode = allProps == null ? Collections.emptyMap()
                : allProps.stream()
                .filter(p -> StrUtil.isNotBlank(p.getPropertyCode()))
                .collect(Collectors.toMap(ProductProperties::getPropertyCode, p -> p, (a, b) -> a));

        Map<String, Object> coerced = new LinkedHashMap<>();
        for (Map.Entry<String, Object> entry : rawProps.entrySet()) {
            String code = entry.getKey();
            Object value = entry.getValue();
            if (StrUtil.isBlank(code) || value == null || "".equals(value)) {
                continue;
            }
            ProductProperties meta = byCode.get(code);
            if (meta != null) {
                String mode = StrUtil.blankToDefault(meta.getMethod(), "").toUpperCase();
                if (!mode.contains("W")) {
                    throw new IllegalArgumentException("属性 " + code + " 不可写");
                }
                coerced.put(code, coercePropertyValue(meta, value));
            } else {
                // 物模型未定义的键透传（兼容自定义字段）
                coerced.put(code, value);
            }
        }
        if (coerced.isEmpty()) {
            throw new IllegalArgumentException("请至少下发一个有效属性值");
        }
        return coerced;
    }

    private Object coercePropertyValue(ProductProperties meta, Object raw) {
        String datatype = StrUtil.blankToDefault(meta.getDatatype(), "string").trim().toLowerCase();
        String text = String.valueOf(raw).trim();
        try {
            switch (datatype) {
                case "int":
                case "int32":
                case "integer":
                case "long": {
                    long num = Long.parseLong(text);
                    if (meta.getMin() != null && num < meta.getMin()) {
                        throw new IllegalArgumentException(meta.getPropertyCode() + " 不能小于 " + meta.getMin());
                    }
                    if (meta.getMax() != null && num > meta.getMax()) {
                        throw new IllegalArgumentException(meta.getPropertyCode() + " 不能大于 " + meta.getMax());
                    }
                    return num;
                }
                case "decimal":
                case "double":
                case "float":
                case "number": {
                    double num = Double.parseDouble(text);
                    if (meta.getMin() != null && num < meta.getMin()) {
                        throw new IllegalArgumentException(meta.getPropertyCode() + " 不能小于 " + meta.getMin());
                    }
                    if (meta.getMax() != null && num > meta.getMax()) {
                        throw new IllegalArgumentException(meta.getPropertyCode() + " 不能大于 " + meta.getMax());
                    }
                    return num;
                }
                case "bool":
                case "boolean": {
                    if ("1".equals(text) || "true".equalsIgnoreCase(text) || "on".equalsIgnoreCase(text)) {
                        return true;
                    }
                    if ("0".equals(text) || "false".equalsIgnoreCase(text) || "off".equalsIgnoreCase(text)) {
                        return false;
                    }
                    throw new IllegalArgumentException(meta.getPropertyCode() + " 必须是布尔值");
                }
                case "jsonobject":
                case "json":
                case "object": {
                    if (raw instanceof Map || raw instanceof List) {
                        return raw;
                    }
                    return JSONObject.parse(text);
                }
                default: {
                    if (meta.getMaxlength() != null && text.length() > meta.getMaxlength()) {
                        throw new IllegalArgumentException(
                                meta.getPropertyCode() + " 长度不能超过 " + meta.getMaxlength());
                    }
                    return text;
                }
            }
        } catch (IllegalArgumentException e) {
            throw e;
        } catch (Exception e) {
            throw new IllegalArgumentException(
                    "属性 " + meta.getPropertyCode() + " 类型应为 " + meta.getDatatype() + "，当前值无效");
        }
    }

    private void mergeDesiredIntoExtension(Device device, Map<String, Object> properties) {
        JSONObject extension = StringUtils.isEmpty(device.getExtension())
                ? new JSONObject() : JSONObject.parseObject(device.getExtension());
        if (extension == null) {
            extension = new JSONObject();
        }

        JSONObject desired = extension.getJSONObject("desired");
        if (desired == null) {
            desired = new JSONObject();
        }
        desired.putAll(properties);
        extension.put("desired", desired);
        extension.put("desiredUpdateTime", LocalDateTime.now()
                .format(DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss")));

        // 同步写入 shadow.desired，便于影子页直接对比
        Object shadowObj = extension.get("shadow");
        JSONObject shadow;
        if (shadowObj instanceof JSONObject) {
            shadow = (JSONObject) shadowObj;
        } else if (shadowObj instanceof Map) {
            @SuppressWarnings("unchecked")
            Map<String, Object> shadowMap = (Map<String, Object>) shadowObj;
            shadow = new JSONObject(shadowMap);
        } else if (shadowObj instanceof String && StrUtil.isNotBlank((String) shadowObj)) {
            shadow = JSONObject.parseObject((String) shadowObj);
        } else {
            shadow = new JSONObject();
        }
        JSONObject shadowDesired = shadow.getJSONObject("desired");
        if (shadowDesired == null) {
            shadowDesired = new JSONObject();
        }
        shadowDesired.putAll(properties);
        shadow.put("desired", shadowDesired);
        if (!shadow.containsKey("reported") && extension.get("properties") != null) {
            shadow.put("reported", extension.get("properties"));
        }
        extension.put("shadow", shadow);

        device.setExtension(extension.toJSONString());
        this.updateById(device);
    }

    @Override
    public List<DeviceCameraLink> listDeviceCameraLinks(Long iotDeviceId) {
        if (iotDeviceId == null) {
            return Collections.emptyList();
        }
        return deviceCameraLinkMapper.selectByIotDeviceId(iotDeviceId);
    }

    @Override
    public List<String> listBoundCameraIds() {
        List<String> ids = deviceCameraLinkMapper.selectAllBoundCameraIds();
        return ids == null ? Collections.emptyList() : ids;
    }

    @Override
    public int associateCameras(Long iotDeviceId, List<String> cameraDeviceIds) {
        if (iotDeviceId == null || cameraDeviceIds == null || cameraDeviceIds.isEmpty()) {
            throw new RuntimeException("关联参数不能为空");
        }
        Device device = deviceMapper.selectDeviceById(iotDeviceId);
        if (device == null) {
            throw new RuntimeException("IoT 设备不存在");
        }
        int successCount = 0;
        LocalDateTime now = LocalDateTime.now();
        for (String cameraDeviceId : cameraDeviceIds) {
            if (StringUtils.isEmpty(cameraDeviceId)) {
                continue;
            }
            DeviceCameraLink existing = deviceCameraLinkMapper.selectByCameraDeviceId(cameraDeviceId);
            if (existing != null) {
                if (iotDeviceId.equals(existing.getIotDeviceId())) {
                    continue;
                }
                // 关联设备已删除时，清理孤儿记录，允许重新关联
                Device linkedDevice = deviceMapper.selectDeviceById(existing.getIotDeviceId());
                if (linkedDevice == null) {
                    deviceCameraLinkMapper.deleteById(existing.getId());
                } else {
                    throw new RuntimeException("摄像头已被其他设备关联: " + cameraDeviceId);
                }
            }
            DeviceCameraLink link = DeviceCameraLink.builder()
                    .iotDeviceId(iotDeviceId)
                    .cameraDeviceId(cameraDeviceId)
                    .tenantId(device.getTenantId())
                    .createTime(now)
                    .updateTime(now)
                    .build();
            if (deviceCameraLinkMapper.insert(link) > 0) {
                successCount++;
            }
        }
        return successCount;
    }

    @Override
    public int disassociateCameras(List<Long> linkIds) {
        if (linkIds == null || linkIds.isEmpty()) {
            throw new RuntimeException("解绑列表不能为空");
        }
        int successCount = 0;
        for (Long linkId : linkIds) {
            if (linkId == null) {
                continue;
            }
            if (deviceCameraLinkMapper.deleteById(linkId) > 0) {
                successCount++;
            }
        }
        return successCount;
    }

    @Override
    public List<DeviceMapLocationVO> listDevicesForMap(boolean hasLocationOnly) {
        List<DeviceMapLocationVO> list = deviceMapper.selectDevicesForMap(hasLocationOnly);
        if (list == null) {
            return List.of();
        }
        for (DeviceMapLocationVO item : list) {
            boolean located = item.getLongitude() != null && item.getLatitude() != null;
            item.setHasLocation(located);
            item.setOnline(DeviceConnectStatusEnum.ONLINE.getValue().equals(item.getConnectStatus()));
        }
        return list;
    }

    @Override
    public DeviceMapLocationVO getDeviceMapLocation(Long deviceId) {
        if (deviceId == null) {
            throw new IllegalArgumentException("设备ID不能为空");
        }
        Device device = deviceMapper.selectDeviceById(deviceId);
        if (device == null) {
            throw new RuntimeException("设备不存在");
        }
        DeviceLocation location = deviceLocationService.findOneByDeviceIdentification(device.getDeviceIdentification());
        DeviceMapLocationVO vo = new DeviceMapLocationVO();
        vo.setId(device.getId());
        vo.setDeviceIdentification(device.getDeviceIdentification());
        vo.setDeviceName(device.getDeviceName());
        vo.setConnectStatus(device.getConnectStatus());
        vo.setOnline(DeviceConnectStatusEnum.ONLINE.getValue().equals(device.getConnectStatus()));
        vo.setDeviceType(device.getDeviceType());
        vo.setProductIdentification(device.getProductIdentification());
        if (location != null) {
            vo.setLongitude(location.getLongitude());
            vo.setLatitude(location.getLatitude());
            vo.setAddress(location.getFullName());
            vo.setLocationUpdatedAt(location.getUpdateTime());
            vo.setHasLocation(location.getLongitude() != null && location.getLatitude() != null);
        } else {
            vo.setHasLocation(false);
        }
        return vo;
    }

    @Override
    public int saveOrUpdateDeviceMapLocation(Long deviceId, DeviceLocationUpdateParam param) {
        if (deviceId == null) {
            throw new IllegalArgumentException("设备ID不能为空");
        }
        if (param == null) {
            throw new IllegalArgumentException("参数不能为空");
        }
        Device device = deviceMapper.selectDeviceById(deviceId);
        if (device == null) {
            throw new RuntimeException("设备不存在");
        }
        String identification = device.getDeviceIdentification();
        DeviceLocation existing = deviceLocationService.findOneByDeviceIdentification(identification);

        // 经纬度都为空：清除坐标
        if (param.getLongitude() == null && param.getLatitude() == null) {
            if (existing == null || existing.getId() == null) {
                return 1;
            }
            return deviceLocationService.deleteDeviceLocationByIds(new Long[]{existing.getId()});
        }
        if (param.getLongitude() == null || param.getLatitude() == null) {
            throw new IllegalArgumentException("经纬度需成对填写");
        }

        LocalDateTime now = LocalDateTime.now();
        if (existing == null) {
            DeviceLocation location = DeviceLocation.builder()
                    .deviceIdentification(identification)
                    .longitude(param.getLongitude())
                    .latitude(param.getLatitude())
                    .fullName(param.getAddress())
                    .provinceCode(param.getProvinceCode())
                    .cityCode(param.getCityCode())
                    .regionCode(param.getRegionCode())
                    .remark(param.getRemark())
                    .createTime(now)
                    .updateTime(now)
                    .build();
            return deviceLocationService.insertDeviceLocation(location);
        }
        existing.setLongitude(param.getLongitude());
        existing.setLatitude(param.getLatitude());
        existing.setUpdateTime(now);
        if (param.getAddress() != null) {
            existing.setFullName(param.getAddress());
        }
        if (param.getProvinceCode() != null) {
            existing.setProvinceCode(param.getProvinceCode());
        }
        if (param.getCityCode() != null) {
            existing.setCityCode(param.getCityCode());
        }
        if (param.getRegionCode() != null) {
            existing.setRegionCode(param.getRegionCode());
        }
        if (param.getRemark() != null) {
            existing.setRemark(param.getRemark());
        }
        return deviceLocationService.updateDeviceLocation(existing);
    }

}
