package com.basiclab.iot.device.service.device.impl;

import cn.hutool.core.bean.BeanUtil;
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
import com.basiclab.iot.common.enums.ResultEnum;
import com.basiclab.iot.common.service.RedisService;
import com.basiclab.iot.sink.biz.IotDownstreamMessageApi;
import com.basiclab.iot.common.utils.DateUtils;
import com.basiclab.iot.common.utils.SnowflakeIdUtil;
import com.basiclab.iot.common.utils.StringUtils;
import com.basiclab.iot.common.utils.bean.BeanPlusUtil;
import com.basiclab.iot.common.utils.tdengine.TdUtils;
import com.basiclab.iot.device.constant.DeviceStatusConstant;
import com.basiclab.iot.device.constant.RedisPrefixConst;
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
import com.basiclab.iot.device.service.device.DeviceLocationService;
import com.basiclab.iot.device.service.device.DeviceService;
import com.basiclab.iot.device.service.device.DeviceTopicService;
import com.basiclab.iot.device.service.product.ProductService;
import com.basiclab.iot.device.service.product.ProductServicesService;
import com.basiclab.iot.file.RemoteFileService;
import com.basiclab.iot.file.domain.vo.SysFileVo;
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

@Service
@Slf4j
@Transactional(isolation = Isolation.DEFAULT, propagation = Propagation.REQUIRES_NEW, rollbackFor = Exception.class)
public class DeviceServiceImpl extends ServiceImpl<DeviceMapper, Device> implements DeviceService {

    @Resource
    private DeviceMapper deviceMapper;
    @Autowired
    private RedisService redisService;
    @Autowired(required = false)
    private IotDownstreamMessageApi iotDownstreamMessageApi;
    @Autowired
    private DeviceTopicService deviceTopicService;
    @Autowired
    private ProductService productService;
    @Autowired
    private DeviceLocationService deviceLocationService;
    @Autowired
    private ProductServicesService productServicesService;
    @Resource
    private RemoteTdEngineService remoteTdEngineService;
    @Resource
    private RemoteFileService remoteFileService;
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
     * 分批插入设备、批次详情记录并更新批次表
     *
     * @param req                请求
     * @param devices            设备列表
     * @param deviceBatchDetails 设备批次详情列表
     * @param response
     * @return 插入成功数量
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
        device.setConnectStatus(DeviceConnectStatusEnum.OFFLINE.getValue());
        device.setDeviceType(product.getProductType());
        final int insertDeviceCount = deviceMapper.insertOrUpdateSelective(device);

        if (insertDeviceCount > 0) {
            //设备位置信息存储
            /*DeviceLocation deviceLocation = new DeviceLocation();
            BeanUtils.copyProperties(deviceParams.getDeviceLocation(), deviceLocation);
            deviceLocation.setDeviceIdentification(device.getDeviceIdentification());
            deviceLocationService.insertOrUpdateSelective(deviceLocation);*/

            //基础TOPIC集合
            Map<String, String> topicMap = new HashMap<>();
            if (DeviceType.GATEWAY.getValue().equals(product.getProductType())) {
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

            } else if (DeviceType.COMMON.getValue().equals(product.getProductType())) {
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
                deviceTopicService.insertSelective(deviceTopic);
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
//        final int insertDeviceCount = deviceMapper.insertOrUpdateSelective(device);
        /*if (insertDeviceCount > 0) {
            //设备位置信息存储
            DeviceLocation deviceLocation = new DeviceLocation();
            BeanUtils.copyProperties(deviceParams.getDeviceLocation(), deviceLocation);
            deviceLocationService.insertOrUpdateSelective(deviceLocation);
        }*/
        return deviceMapper.updateDevice(device);
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
        //校验目标设备是否是网关
        Device device = deviceMapper.findOneByDeviceIdentification(targetDeviceIdentification);
        if (!Device.deviceTypeEnum.GATEWAY.getType().equals(device.getDeviceType())) {
            throw new RuntimeException("目标关联设备非网关设备");
        }
        //校验设备id列表是否全部是子设备 todo
        ArrayList<Device> devices = new ArrayList<>();
        for (Long id : idList) {
            Device deviceTmp = new Device();
            deviceTmp.setId(id);
            deviceTmp.setParentIdentification(targetDeviceIdentification);
            devices.add(deviceTmp);
        }
        return deviceMapper.updateBatch(devices);
    }

    @Override
    public int disassociateGateway(List<Long> idList) {
        ArrayList<Device> devices = new ArrayList<>();
        for (Long id : idList) {
            Device deviceTmp = new Device();
            deviceTmp.setId(id);
            deviceTmp.setParentIdentification("");
            devices.add(deviceTmp);
        }
        return deviceMapper.updateBatch(devices);
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

}

