package com.basiclab.iot.device.controller.device;

import com.basiclab.iot.common.adapter.ExcelUtil;
import com.basiclab.iot.common.domain.AjaxResult;
import com.basiclab.iot.common.domain.TableDataInfo;
import com.basiclab.iot.common.utils.SecurityUtils;
import com.basiclab.iot.common.web.controller.BaseController;
import com.basiclab.iot.device.domain.device.vo.DeviceLocation;
import com.basiclab.iot.device.service.device.DeviceLocationService;
import org.springframework.web.bind.annotation.*;

import javax.annotation.Resource;
import javax.servlet.http.HttpServletResponse;
import java.io.IOException;
import java.util.List;

/**
 * 设备位置信息Controller
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@RestController
@RequestMapping("deviceLocation")
public class DeviceLocationController extends BaseController {
    /**
     * 服务对象
     */
    @Resource
    private DeviceLocationService deviceLocationService;

    /**
     * 通过主键查询单条数据
     *
     * @param id 主键
     * @return 单条数据
     */
    @GetMapping("selectOne")
    public DeviceLocation selectOne(Integer id) {
        return deviceLocationService.selectDeviceLocationById(Long.valueOf(id));
    }

    /**
     * 查询设备位置列表
     */
    //@PreAuthorize(hasPermi = "link:deviceLocation:list")
    @GetMapping("/list")
    public TableDataInfo list(DeviceLocation deviceLocation) {
        startPage();
        List<DeviceLocation> list = deviceLocationService.selectDeviceLocationList(deviceLocation);
        return getDataTable(list);
    }

    /**
     * 导出设备位置列表
     */
    //@PreAuthorize(hasPermi = "link:deviceLocation:export")
    //@Log(title = "设备位置", businessType = BusinessType.EXPORT)
    @PostMapping("/export")
    public void export(HttpServletResponse response, DeviceLocation deviceLocation) throws IOException {
        List<DeviceLocation> list = deviceLocationService.selectDeviceLocationList(deviceLocation);
        ExcelUtil<DeviceLocation> util = new ExcelUtil<DeviceLocation>(DeviceLocation.class);
        util.exportExcel(response, list, "设备位置数据");
    }

    /**
     * 获取设备位置详细信息
     */
    //@PreAuthorize(hasPermi = "link:deviceLocation:query")
    @GetMapping(value = "/{id}")
    public AjaxResult getInfo(@PathVariable("id") Long id) {
        return AjaxResult.success(deviceLocationService.selectDeviceLocationById(id));
    }

    /**
     * 新增设备位置
     */
    //@PreAuthorize(hasPermi = "link:deviceLocation:add")
    //@Log(title = "设备位置", businessType = BusinessType.INSERT)
    @PostMapping
    public AjaxResult add(@RequestBody DeviceLocation deviceLocation) {
        deviceLocation.setCreateBy(SecurityUtils.getUsername());
        return toAjax(deviceLocationService.insertDeviceLocation(deviceLocation));
    }

    /**
     * 修改设备位置
     */
    //@PreAuthorize(hasPermi = "link:deviceLocation:edit")
    //@Log(title = "设备位置", businessType = BusinessType.UPDATE)
    @PutMapping
    public AjaxResult edit(@RequestBody DeviceLocation deviceLocation) {
        deviceLocation.setUpdateBy(SecurityUtils.getUsername());
        return toAjax(deviceLocationService.updateDeviceLocation(deviceLocation));
    }

    /**
     * 删除设备位置
     */
    //@PreAuthorize(hasPermi = "link:deviceLocation:remove")
    //@Log(title = "设备位置", businessType = BusinessType.DELETE)
    @DeleteMapping("/{ids}")
    public AjaxResult remove(@PathVariable Long[] ids) {
        return toAjax(deviceLocationService.deleteDeviceLocationByIds(ids));
    }
}
