package com.basiclab.iot.device.controller.device;

import com.basiclab.iot.common.domain.TableDataInfo;
import com.basiclab.iot.common.web.controller.BaseController;
import com.basiclab.iot.device.domain.device.vo.TDDeviceDataResp;
import com.basiclab.iot.device.service.device.DeviceThingModelService;
import io.swagger.annotations.ApiImplicitParam;
import io.swagger.annotations.ApiImplicitParams;
import io.swagger.annotations.ApiOperation;
import io.swagger.v3.oas.annotations.tags.Tag;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import javax.annotation.Resource;
import java.util.List;

/**
 * DeviceThingModelController
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */

@Tag(name  = "设备运行状态管理")
@RestController
@RequestMapping("/deviceThingModel")
public class DeviceThingModelController extends BaseController {

    @Resource
    private DeviceThingModelService deviceThingModelService;

    @ApiOperation("获取设备运行状态")
    @ApiImplicitParams({
            @ApiImplicitParam(name = "pageNum", value = "页码", dataType = "int", dataTypeClass = Integer.class, paramType = "query", example = "1", required = true),
            @ApiImplicitParam(name = "pageSize", value = "每页显示记录数", dataType = "int", dataTypeClass = Integer.class, paramType = "query", example = "10", required = true),
            @ApiImplicitParam(name = "orderByColumn", value = "排序字段", dataType = "string", dataTypeClass = String.class, paramType = "query"),
            @ApiImplicitParam(name = "isAsc", value = "排序方式（asc/desc）", dataType = "string", dataTypeClass = String.class, paramType = "query")
    })
    @GetMapping(value = "/runtimeStatus")
    // @PreAuthorize("@ss.hasPermission('link:deviceThingModel:query')")
    public TableDataInfo getRuntimeStatus(@RequestParam("id") Long id, String name){
        startPage();
        List<TDDeviceDataResp> list = deviceThingModelService.getDeviceThingModels(id, name);
        return getDataTable(list);
    }



}
