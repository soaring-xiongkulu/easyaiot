package com.basiclab.iot.device.controller.admin.device;

import com.basiclab.iot.device.common.BaseController;
import com.basiclab.iot.device.common.TableDataInfo;
import com.basiclab.iot.device.controller.admin.device.vo.TDDeviceDataResp;
import com.basiclab.iot.device.service.product_properties.DeviceThingModelService;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import javax.annotation.Resource;
import java.util.List;

/**
 * (deviceProperties)设备运行状态管理
 *
 * @author basiclab
 */
@RestController
@RequestMapping("/deviceThingModel")
public class DeviceThingModelController extends BaseController {

    @Resource
    private DeviceThingModelService deviceThingModelService;

    //获取设备运行状态
    @GetMapping(value = "/runtimeStatus")
    @PreAuthorize("@ss.hasPermission('link:deviceThingModel:query')")
    public TableDataInfo getRuntimeStatus(@RequestParam("id") Long id, String name) {
        startPage();
        List<TDDeviceDataResp> list = deviceThingModelService.getDeviceThingModels(id, name);
        return getDataTable(list);
    }


}
