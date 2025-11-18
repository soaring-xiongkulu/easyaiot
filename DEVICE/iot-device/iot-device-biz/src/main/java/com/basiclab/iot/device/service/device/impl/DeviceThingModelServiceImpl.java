package com.basiclab.iot.device.service.device.impl;

import cn.hutool.core.bean.BeanUtil;
import com.basiclab.iot.common.domain.R;
import com.basiclab.iot.device.constant.FunctionTypeConstant;
import com.basiclab.iot.device.constant.TdengineConstant;
import com.basiclab.iot.device.domain.device.vo.Device;
import com.basiclab.iot.device.domain.device.vo.Product;
import com.basiclab.iot.device.domain.device.vo.ProductProperties;
import com.basiclab.iot.device.domain.device.vo.TDDeviceDataResp;
import com.basiclab.iot.device.service.device.DeviceService;
import com.basiclab.iot.device.service.device.DeviceThingModelService;
import com.basiclab.iot.device.service.product.ProductPropertiesService;
import com.basiclab.iot.device.service.product.ProductService;
import com.basiclab.iot.tdengine.RemoteTdEngineService;
import com.basiclab.iot.tdengine.domain.DeviceData;
import com.basiclab.iot.tdengine.domain.query.TDDeviceDataRequest;
import org.apache.commons.compress.utils.Lists;
import org.springframework.stereotype.Service;
import org.springframework.util.CollectionUtils;

import javax.annotation.Resource;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;
import java.util.stream.Collectors;

/**
 * DeviceThingModelServiceImpl
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Service
public class DeviceThingModelServiceImpl implements DeviceThingModelService {

    @Resource
    private RemoteTdEngineService tdEngineService;
    @Resource
    private ProductPropertiesService productPropertiesService;
    @Resource
    private DeviceService deviceService;
    @Resource
    private ProductService productService;

    //设备详情-运行状态
    @Override
    public List<TDDeviceDataResp> getDeviceThingModels(Long id, String name) {
        //先查产品物模型
        Device device = deviceService.selectDeviceById(id);
        Product product = productService.selectByProductIdentification(device.getProductIdentification());
        ProductProperties productProperties = new ProductProperties();
        productProperties.setTemplateIdentification(product.getTemplateIdentification());
        productProperties.setProductIdentification(product.getProductIdentification());
        productProperties.setPropertyCode(name);
        productProperties.setPropertyName(name);
        List<ProductProperties> productPropertiesList = productPropertiesService.selectProductPropertiesList(productProperties);
        if (productPropertiesList.isEmpty()) {
            return Lists.newArrayList();
        }
        List<TDDeviceDataResp> result = BeanUtil.copyToList(productPropertiesList, TDDeviceDataResp.class);
        List<String> propertyCode = result.stream().map(TDDeviceDataResp::getPropertyCode).collect(Collectors.toList());
        //从td数据库查设备属性数据
        TDDeviceDataRequest request = new TDDeviceDataRequest();
        request.setDeviceIdentification(device.getDeviceIdentification());
        request.setIdentifierList(propertyCode);
        request.setFunctionType(FunctionTypeConstant.PROPERTIES);
        request.setTdDatabaseName(TdengineConstant.IOT_DEVICE);
        request.setTdSuperTableName(TdengineConstant.DEVICE_DATA);
        List<DeviceData> deviceData = new ArrayList<>();
        R<List<DeviceData>> lastRowsListByIdentifier = tdEngineService.getLastRowsListByIdentifier(request);
        if (lastRowsListByIdentifier != null && lastRowsListByIdentifier.getData() != null) {
            deviceData = lastRowsListByIdentifier.getData();
        }
        if (!CollectionUtils.isEmpty(deviceData)) {
            for (TDDeviceDataResp resp : result) {
                for (DeviceData tdDeviceDataResp : deviceData) {
                    if (resp.getPropertyCode().equals(tdDeviceDataResp.getIdentifier())) {
                        resp.setTs(tdDeviceDataResp.getLastUpdateTime());
                        resp.setDataValue(tdDeviceDataResp.getDataValue());
                    }
                }
            }
            //最后上报时间排序
            result.sort(Comparator.comparing(TDDeviceDataResp::getTs, Comparator.nullsFirst(Comparator.naturalOrder())).reversed());
        }
        return result;
    }

}
