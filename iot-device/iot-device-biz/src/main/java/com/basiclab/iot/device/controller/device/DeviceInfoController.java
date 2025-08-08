package com.basiclab.iot.device.controller.device;

import com.basiclab.iot.common.adapter.ExcelUtil;
import com.basiclab.iot.common.domain.AjaxResult;
import com.basiclab.iot.common.domain.TableDataInfo;
import com.basiclab.iot.common.web.controller.BaseController;
import com.basiclab.iot.device.domain.device.vo.DeviceInfo;
import com.basiclab.iot.device.domain.device.vo.DeviceInfoParams;
import com.basiclab.iot.device.service.device.DeviceInfoService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

import javax.servlet.http.HttpServletResponse;
import javax.validation.Valid;
import java.io.IOException;
import java.util.List;
import java.util.Map;

/**
 * 子设备管理Controller
 *
 * @author EasyAIoT
 * @date 2022-06-21
 */
@RestController
@RequestMapping("/deviceInfo")
public class DeviceInfoController extends BaseController {
    @Autowired
    private DeviceInfoService deviceInfoService;

    /**
     * 查询子设备管理列表
     */
    //@PreAuthorize(hasPermi = "link:deviceInfo:list")
    @GetMapping("/list")
    public TableDataInfo list(DeviceInfo deviceInfo) {
        startPage();
        List<DeviceInfo> list = deviceInfoService.selectDeviceInfoList(deviceInfo);
        return getDataTable(list);
    }

    /**
     * 导出子设备管理列表
     */
    //@PreAuthorize(hasPermi = "link:deviceInfo:export")
    //@Log(title = "子设备管理", businessType = BusinessType.EXPORT)
    @PostMapping("/export")
    public void export(HttpServletResponse response, DeviceInfo deviceInfo) throws IOException {
        List<DeviceInfo> list = deviceInfoService.selectDeviceInfoList(deviceInfo);
        ExcelUtil<DeviceInfo> util = new ExcelUtil<DeviceInfo>(DeviceInfo.class);
        util.exportExcel(response, list, "子设备管理数据");
    }

    /**
     * 获取子设备管理详细信息
     */
    //@PreAuthorize(hasPermi = "link:deviceInfo:query")
    @GetMapping(value = "/{id}")
    public AjaxResult getInfo(@PathVariable("id") Long id) {
        return AjaxResult.success(deviceInfoService.selectDeviceInfoById(id));
    }

    /**
     * 新增子设备管理
     */
    //@PreAuthorize(hasPermi = "link:deviceInfo:add")
    //@Log(title = "子设备管理", businessType = BusinessType.INSERT)
    @PostMapping
    public AjaxResult add(@RequestBody @Valid DeviceInfoParams deviceInfoParams) {
        return toAjax(deviceInfoService.insertDeviceInfo(deviceInfoParams));
    }

    /**
     * 修改子设备管理
     */
    //@PreAuthorize(hasPermi = "link:deviceInfo:edit")
    //@Log(title = "子设备管理", businessType = BusinessType.UPDATE)
    @PutMapping
    public AjaxResult edit(@RequestBody @Valid DeviceInfoParams deviceInfoParams) {
        return toAjax(deviceInfoService.updateDeviceInfo(deviceInfoParams));
    }

    /**
     * 删除子设备管理
     */
    //@PreAuthorize(hasPermi = "link:deviceInfo:remove")
    //@Log(title = "子设备管理", businessType = BusinessType.DELETE)
    @DeleteMapping("/{ids}")
    public AjaxResult remove(@PathVariable("ids") Long[] ids) {
        return toAjax(deviceInfoService.deleteDeviceInfoByIds(ids));
    }

    /**
     * 查询子设备影子数据
     *
     * @param params
     * @return
     */
    //@PreAuthorize(hasPermi = "link:deviceInfo:shadow")
    @PostMapping(value = "/getDeviceInfoShadow")
    public AjaxResult getDeviceInfoShadow(@RequestBody Map<String, Object> params) {
        final Object ids = params.get("ids");
        final Object startTime = params.get("startTime");
        final Object endTime = params.get("endTime");
        return AjaxResult.success(deviceInfoService.getDeviceInfoShadow(ids.toString(), startTime.toString(), endTime.toString()));
    }


}
