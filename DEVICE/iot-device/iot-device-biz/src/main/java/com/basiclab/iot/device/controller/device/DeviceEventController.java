package com.basiclab.iot.device.controller.device;

import com.basiclab.iot.common.domain.AjaxResult;
import com.basiclab.iot.common.domain.R;
import com.basiclab.iot.common.domain.TableDataInfo;
import com.basiclab.iot.common.web.controller.BaseController;
import com.basiclab.iot.device.domain.device.vo.DeviceEvent;
import com.basiclab.iot.device.service.device.DeviceEventService;
import io.swagger.annotations.Api;
import io.swagger.annotations.ApiOperation;
import org.springframework.web.bind.annotation.*;

import javax.annotation.Resource;
import java.util.List;

/**
 * DeviceEventController
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Api(tags = "设备事件管理")
@RestController
@RequestMapping("/deviceEvent")
public class DeviceEventController extends BaseController {

    @Resource
    private DeviceEventService deviceEventService;

    /**
     * 查询设备事件列表
     */
    @ApiOperation("查询设备事件列表")
    @GetMapping("/list")
    public TableDataInfo list(DeviceEvent deviceEvent) {
        startPage();
        List<DeviceEvent> list = deviceEventService.selectDeviceEventList(deviceEvent);
        return getDataTable(list);
    }

    /**
     * 获取设备事件详细信息
     */
    @ApiOperation("获取设备事件详细信息")
    @GetMapping(value = "/{id}")
    public AjaxResult getInfo(@PathVariable("id") Long id) {
        return AjaxResult.success(deviceEventService.selectDeviceEventById(id));
    }

    /**
     * 新增设备事件
     */
    @ApiOperation("新增设备事件")
    @PostMapping
    public AjaxResult add(@RequestBody DeviceEvent deviceEvent) {
        return toAjax(deviceEventService.insertDeviceEvent(deviceEvent));
    }

    /**
     * 修改设备事件
     */
    @ApiOperation("修改设备事件")
    @PutMapping
    public AjaxResult edit(@RequestBody DeviceEvent deviceEvent) {
        return toAjax(deviceEventService.updateDeviceEvent(deviceEvent));
    }

    /**
     * 删除设备事件
     */
    @ApiOperation("删除设备事件")
    @DeleteMapping("/{ids}")
    public AjaxResult remove(@PathVariable String[] ids) {
        return toAjax(deviceEventService.deleteDeviceEventByIds(ids));
    }
}

