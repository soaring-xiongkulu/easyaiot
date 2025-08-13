package com.basiclab.iot.device.controller.device;

import com.basiclab.iot.common.adapter.ExcelUtil;
import com.basiclab.iot.common.domain.AjaxResult;
import com.basiclab.iot.common.domain.TableDataInfo;
import com.basiclab.iot.common.web.controller.BaseController;
import com.basiclab.iot.device.domain.device.vo.DeviceTopic;
import com.basiclab.iot.device.service.device.DeviceTopicService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

import javax.servlet.http.HttpServletResponse;
import java.io.IOException;
import java.util.List;

/**
 * 设备Topic数据Controller
 *
 * @author EasyAIoT
 * @date 2022-06-17
 */
@RestController
@RequestMapping("/topic")
public class DeviceTopicController extends BaseController {
    @Autowired
    private DeviceTopicService deviceTopicService;

    /**
     * 查询设备Topic数据列表
     */
    //@PreAuthorize(hasPermi = "link:topic:list")
    @GetMapping("/list")
    public TableDataInfo list(DeviceTopic deviceTopic) {
        startPage();
        List<DeviceTopic> list = deviceTopicService.selectDeviceTopicList(deviceTopic);
        return getDataTable(list);
    }

    /**
     * 导出设备Topic数据列表
     */
    //@PreAuthorize(hasPermi = "link:topic:export")
    //@Log(title = "设备Topic数据", businessType = BusinessType.EXPORT)
    @PostMapping("/export")
    public void export(HttpServletResponse response, DeviceTopic deviceTopic) throws IOException {
        List<DeviceTopic> list = deviceTopicService.selectDeviceTopicList(deviceTopic);
        ExcelUtil<DeviceTopic> util = new ExcelUtil<DeviceTopic>(DeviceTopic.class);
        util.exportExcel(response, list, "设备Topic数据数据");
    }

    /**
     * 获取设备Topic数据详细信息
     */
    //@PreAuthorize(hasPermi = "link:topic:query")
    @GetMapping(value = "/{id}")
    public AjaxResult getInfo(@PathVariable("id") Long id) {
        return AjaxResult.success(deviceTopicService.selectDeviceTopicById(id));
    }

    /**
     * 新增设备Topic数据
     */
    //@PreAuthorize(hasPermi = "link:topic:add")
    //@Log(title = "设备Topic数据", businessType = BusinessType.INSERT)
    @PostMapping
    public AjaxResult add(@RequestBody DeviceTopic deviceTopic) {
        return toAjax(deviceTopicService.insertDeviceTopic(deviceTopic));
    }

    /**
     * 修改设备Topic数据
     */
    //@PreAuthorize(hasPermi = "link:topic:edit")
    //@Log(title = "设备Topic数据", businessType = BusinessType.UPDATE)
    @PutMapping
    public AjaxResult edit(@RequestBody DeviceTopic deviceTopic) {
        return toAjax(deviceTopicService.updateDeviceTopic(deviceTopic));
    }

    /**
     * 删除设备Topic数据
     */
    //@PreAuthorize(hasPermi = "link:topic:remove")
    //@Log(title = "设备Topic数据", businessType = BusinessType.DELETE)
    @DeleteMapping("/{ids}")
    public AjaxResult remove(@PathVariable Long[] ids) {
        return toAjax(deviceTopicService.deleteDeviceTopicByIds(ids));
    }
}