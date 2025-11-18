package com.basiclab.iot.device.controller.device;

import com.alibaba.fastjson2.JSONObject;
import com.basiclab.iot.common.adapter.ExcelUtil;
import com.basiclab.iot.common.annotation.NoRepeatSubmit;
import com.basiclab.iot.common.domain.AjaxResult;
import com.basiclab.iot.common.domain.R;
import com.basiclab.iot.common.domain.TableDataInfo;
import com.basiclab.iot.common.utils.SnowflakeIdUtil;
import com.basiclab.iot.common.utils.StringUtils;
import com.basiclab.iot.common.web.controller.BaseController;
import com.basiclab.iot.device.constant.DeviceStatusConstant;
import com.basiclab.iot.device.domain.device.oo.DeviceReportOo;
import com.basiclab.iot.device.domain.device.qo.DeviceAlarmQo;
import com.basiclab.iot.device.domain.device.qo.DeviceIsExistQo;
import com.basiclab.iot.device.domain.device.vo.*;
import com.basiclab.iot.device.enums.device.DeviceConnectStatusEnum;
import com.basiclab.iot.device.service.device.DeviceService;
import com.basiclab.iot.device.service.product.ProductService;
import io.swagger.annotations.ApiImplicitParam;
import io.swagger.annotations.ApiImplicitParams;
import io.swagger.annotations.ApiOperation;
import io.swagger.annotations.ApiParam;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.extern.slf4j.Slf4j;
import org.apache.commons.collections4.CollectionUtils;
import org.springframework.http.ResponseEntity;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.*;

import javax.annotation.Resource;
import javax.servlet.http.HttpServletResponse;
import javax.validation.constraints.NotEmpty;
import java.io.IOException;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

/**
 * DeviceController
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Tag(name = "设备管理")
@RestController
@RequestMapping("/device")
@Slf4j
public class DeviceController extends BaseController {
    @Resource
    private DeviceService deviceService;
    @Resource
    private ProductService productService;

    @PostMapping("/isExist")
    @ApiOperation("判断设备是否存在")
    public R<Boolean> isExist(@RequestBody DeviceIsExistQo deviceIsExistQo) {
        try {
            return R.ok(deviceService.isExist(deviceIsExistQo));
        } catch (Exception e) {
            log.error("判断设备是否存在失败:{}", deviceIsExistQo, e);
            return R.fail("判断设备是否存在失败");
        }
    }

    @PostMapping("/alarm")
    @ApiOperation("边缘网关告警")
    public R<String> alarm(@RequestBody DeviceAlarmQo data) {
        try {
            log.info("收到边缘网关告警, params=" + JSONObject.toJSONString(data));
        } catch (Exception e) {
            log.error("边缘网关告警失败:{}",
                    data, e);
            return R.fail("边缘网关告警失败");
        }
        return R.ok("边缘网关告警成功");
    }

    @PostMapping("/report")
    @ApiOperation("设备上报")
    public R<String> report(@ApiParam("设备上报实体") @Validated @NotEmpty @RequestBody DeviceReportOo deviceReportOo) {
        try {
            log.info("设备上报, params=" + JSONObject.toJSONString(deviceReportOo));
            deviceService.report(deviceReportOo);
        } catch (Exception e) {
            log.error("设备上报数据失败:{}",
                    deviceReportOo, e);
            return R.fail("设备上报当前版本失败");
        }
        return R.ok("设备上报当前版本成功");
    }

    /**
     * emqx的WebHook机制的回调地址
     *
     * @param params
     */
    @ApiOperation("EMQX钩子回调")
    @PostMapping("/webHook")
    public void webHook(@RequestBody Map<String, Object> params) {
        log.info("EMQX钩子回调, params=" + params);
        String action = (String) params.get("event");
        if (StringUtils.isEmpty(action)) return;
        if (DeviceStatusConstant.CLIENT_CONNECTED.equals(action)) {
            deviceService.handleConnected(params);
        } else if (DeviceStatusConstant.CLIENT_DISCONNECTED.equals(action)) {
            deviceService.handleDisConnected(params);
        } else if (DeviceStatusConstant.SESSION_SUBSCRIBED.equals(action)) {
            deviceService.handleSubscribe(params);
        }
    }


    /**
     * 查询设备管理列表
     */
    @ApiOperation("查询设备列表")
    @ApiImplicitParams({
            @ApiImplicitParam(name = "pageNum", value = "页码", dataType = "int", dataTypeClass = Integer.class, paramType = "query", example = "1", required = true),
            @ApiImplicitParam(name = "pageSize", value = "每页显示记录数", dataType = "int", dataTypeClass = Integer.class, paramType = "query", example = "10", required = true),
            @ApiImplicitParam(name = "orderByColumn", value = "排序字段", dataType = "string", dataTypeClass = String.class, paramType = "query"),
            @ApiImplicitParam(name = "isAsc", value = "排序方式（asc/desc）", dataType = "string", dataTypeClass = String.class, paramType = "query")
    })
    // @PreAuthorize("@ss.hasPermission('link:device:list')")
    @GetMapping("/list")
    public TableDataInfo list(Device device) {
        startPage();
        List<Device> list = deviceService.selectDeviceList(device);
        return getDataTable(list);
    }

    /**
     * 通过主产品标识查询产品
     *
     * @param productIdentification 产品标识
     * @return 单条数据
     */
    @GetMapping("/selectByProductIdentification/{productIdentification}")
    public R<?> selectByProductIdentification(@PathVariable(value = "productIdentification") String productIdentification) {
        return R.ok(deviceService.findAllByProductIdentification(productIdentification));
    }

    /**
     * 通过主产品标识查询产品
     *
     * @param productIdentification 产品标识
     * @return 单条数据
     */
    @GetMapping("/selectByProductIdentificationAndDeviceIdentification/{productIdentification}/{deviceIdentification}")
    public R<?> selectByProductIdentificationAndDeviceIdentification(@PathVariable(value = "productIdentification") String productIdentification
            , @PathVariable(value = "deviceIdentification") String deviceIdentification) {
        return R.ok(deviceService.selectByProductIdentificationAndDeviceIdentification(productIdentification, deviceIdentification));
    }

    /**
     * 获取设备列表对应各个状态的设备数量
     *
     * @param device
     * @return
     */
    // @PreAuthorize("@ss.hasPermission('link:device:count')")
    @GetMapping("/listStatusCount")
    public AjaxResult listStatusCount(Device device) {

        Map<String, List<Device>> connectStatusCollect = deviceService.selectDeviceList(device).parallelStream().collect(Collectors.groupingBy(Device::getConnectStatus));

        Map<String, Integer> countMap = new HashMap<>();
        //统计设备在线数量
        countMap.put("onlineCount", !connectStatusCollect.isEmpty() && !CollectionUtils.isEmpty(connectStatusCollect.get(DeviceConnectStatusEnum.ONLINE.getValue())) ? connectStatusCollect.get(DeviceConnectStatusEnum.ONLINE.getValue()).size() : 0);
        //统计设备离线数量
        countMap.put("offlineCount", !connectStatusCollect.isEmpty() && !CollectionUtils.isEmpty(connectStatusCollect.get(DeviceConnectStatusEnum.OFFLINE.getValue())) ? connectStatusCollect.get(DeviceConnectStatusEnum.OFFLINE.getValue()).size() : 0);
        //统计设备初始化数量
        countMap.put("initCount", !connectStatusCollect.isEmpty() && !CollectionUtils.isEmpty(connectStatusCollect.get(DeviceConnectStatusEnum.INIT.getValue())) ? connectStatusCollect.get(DeviceConnectStatusEnum.INIT.getValue()).size() : 0);

        return AjaxResult.success(countMap);
    }

    /**
     * 导出设备管理列表
     */
    // @PreAuthorize("@ss.hasPermission('link:device:export')")

    /// /@Log(title = "设备管理", businessType = BusinessType.EXPORT)
    @PostMapping("/export")
    public void export(HttpServletResponse response, Device device) throws IOException {
        List<Device> list = deviceService.selectDeviceList(device);
        ExcelUtil<Device> util = new ExcelUtil<Device>(Device.class);
        util.exportExcel(response, list, "设备管理数据");
    }

    /**
     * 获取设备管理详细信息
     */
    @ApiOperation("获取设备详细信息")
    // @PreAuthorize("@ss.hasPermission('link:device:query')")
    @GetMapping(value = "/{id}")
    public AjaxResult getInfo(@PathVariable("id") Long id) {
        AjaxResult ajax = AjaxResult.success();
        DeviceParams deviceParams = deviceService.selectDeviceModelById(id);
        DeviceDetail result = new DeviceDetail();
        result.setDevice(deviceParams);
        result.setProduct(productService.selectByProductIdentification(deviceParams.getProductIdentification()));
        ajax.put(AjaxResult.DATA_TAG, result);
        return ajax;
    }

    /**
     * 新增设备管理
     */
    @ApiOperation("添加设备")
    @NoRepeatSubmit
    // @PreAuthorize("@ss.hasPermission('link:device:add')")
    ////@Log(title = "设备管理", businessType = BusinessType.INSERT)
    @PostMapping
    public AjaxResult add(@RequestBody Device device) {
        try {
            device.setDeviceIdentification(SnowflakeIdUtil.nextId());
            return toAjax(deviceService.insertDevice(device));
        } catch (Exception e) {
            return AjaxResult.error(e.getMessage());
        }
    }

    /**
     * 修改设备管理
     */
    @ApiOperation("编辑设备信息")
    @NoRepeatSubmit
    // @PreAuthorize("@ss.hasPermission('link:device:edit')")
    ////@Log(title = "设备管理", businessType = BusinessType.UPDATE)
    @PutMapping
    public AjaxResult edit(@RequestBody Device device) {
        try {
            return toAjax(deviceService.updateDevice(device));
        } catch (Exception e) {
            return AjaxResult.error(e.getMessage());
        }
    }

    /**
     * 查询设备扩展信息
     */
    @ApiOperation("查询设备扩展信息")
    @PostMapping("/extension/query")
    public R<DeviceExtensionDataVO> queryDeviceExtensionData(@Validated @RequestBody DeviceExtensionQueryRequest request) {
        try {
            DeviceExtensionDataVO result = deviceService.queryDeviceExtensionData(request);
            if (result == null) {
                return R.fail("设备不存在或扩展信息为空");
            }
            return R.ok(result);
        } catch (Exception e) {
            log.error("查询设备扩展信息失败：{}", e.getMessage(), e);
            return R.fail("查询设备扩展信息失败：" + e.getMessage());
        }
    }

    /**
     * 删除设备管理
     */
    @ApiOperation("删除设备")
    // @PreAuthorize("@ss.hasPermission('link:device:remove')")
    ////@Log(title = "设备管理", businessType = BusinessType.DELETE)
    @DeleteMapping("/{ids}")
    public AjaxResult remove(@PathVariable Long[] ids) {
        return toAjax(deviceService.deleteDeviceByIds(ids));
    }

    /**
     * 更新设备在线状态
     */
    @PutMapping("/updateConnectStatusByClientId")
    public R updateConnectStatusByClientId(@RequestBody Device device) {
        return R.ok(deviceService.updateConnectStatusByClientId(device.getConnectStatus(), device.getClientId()));
    }

    /**
     * 校验clientId是否存在
     *
     * @param clientId
     * @return
     */
    /// /@Log(title = "设备管理", businessType = BusinessType.OTHER)
    @GetMapping(value = "/validationFindOneByClientId/{clientId}")
    public AjaxResult validationFindOneByClientId(@PathVariable("clientId") String clientId) {
        if (StringUtils.isEmpty(clientId)) {
            return AjaxResult.error("clientId不可为空");
        }
        Device findOneByClientId = deviceService.findOneByClientId(clientId);
        if (StringUtils.isNull(findOneByClientId)) {
            return AjaxResult.success("clientId可用");
        }
        return AjaxResult.error("clientId已存在");
    }

    /**
     * 校验设备标识是否存在
     *
     * @param deviceIdentification
     * @return
     */
    /// /@Log(title = "设备管理", businessType = BusinessType.OTHER)
    @GetMapping(value = "/validationFindOneByDeviceIdentification/{deviceIdentification}")
    public AjaxResult validationFindOneByDeviceIdentification(@PathVariable("deviceIdentification") String deviceIdentification) {
        if (StringUtils.isEmpty(deviceIdentification)) {
            return AjaxResult.error("设备标识不可为空");
        }
        Device findOneByDeviceIdentification = deviceService.findOneByDeviceIdentification(deviceIdentification);
        if (StringUtils.isNull(findOneByDeviceIdentification)) {
            return AjaxResult.success("设备标识可用");
        }
        return AjaxResult.error("设备标识已存在");
    }


    /**
     * 设备断开连接接口
     */
    // @PreAuthorize("@ss.hasPermission('link:device:disconnect')")

    /// /@Log(title = "设备管理", businessType = BusinessType.OTHER)
    @PostMapping("/disconnect/{ids}")
    public AjaxResult disconnect(@PathVariable Long[] ids) {
        final Boolean disconnect = deviceService.disconnect(ids);
        return disconnect ? AjaxResult.success("操作成功") : AjaxResult.error("操作失败");
    }

    /**
     * smqttx客户端身份认证
     *
     * @param params
     * @return
     */
    @Deprecated
    @PostMapping("/clientAuthentication")
    public ResponseEntity<AjaxResult> clientAuthentication(@RequestBody Map<String, Object> params) {
        final Object clientIdentifier = params.get("clientIdentifier");
        final Object username = params.get("username");
        final Object password = params.get("password");
        final Object deviceStatus = params.get("deviceStatus");
        final Object protocolType = params.get("protocolType");

        Device device = deviceService.clientAuthentication(clientIdentifier.toString(), username.toString(), password.toString(), deviceStatus.toString(), protocolType.toString());
        log.info("{} 协议设备正在进行身份认证,客户端ID:{},用户名:{},密码:{},认证结果:{}", protocolType, clientIdentifier, username, password, device != null ? "成功" : "失败");

        return device != null ? ResponseEntity.ok().body(AjaxResult.success("认证成功")) : ResponseEntity.status(403).body(AjaxResult.error("认证失败"));
    }

    /**
     * 根据客户端标识获取设备信息
     *
     * @param clientId
     * @return
     */
    @PostMapping("/findOneByClientId")
    public R<Device> findOneByClientId(@RequestBody String clientId) {
        return R.ok(deviceService.findOneByClientId(clientId));
    }


    /**
     * 根据产品标识获取产品所有关联设备
     *
     * @param productIdentification
     * @return
     */
    @GetMapping("/selectAllByProductIdentification/{productIdentification}")
    public R<List<Device>> selectAllByProductIdentification(@PathVariable(value = "productIdentification") String productIdentification) {
        return R.ok(deviceService.findAllByProductIdentification(productIdentification));
    }


    @PostMapping("/selectDeviceByDeviceIdentificationList")
    public R<?> selectDeviceByDeviceIdentificationList(@RequestBody List<String> deviceIdentificationList) {
        return R.ok(deviceService.selectDeviceByDeviceIdentificationList(deviceIdentificationList));
    }

    @ApiOperation("关联网关")
    @PostMapping("/associateGateway")
    public AjaxResult associateGateway(@RequestBody AssociateGatewayRequest associateGatewayRequest) {
        int successCount = deviceService.associateGateway(associateGatewayRequest.getIdList(), associateGatewayRequest.getTargetDeviceIdentification());
        if (successCount == 0) {
            return AjaxResult.error("关联失败");
        }
        return AjaxResult.success();
    }

    @ApiOperation("解除关联")
    @PostMapping("/disassociateGateway")
    public AjaxResult disassociateGateway(@RequestBody List<Long> idList) {
        int successCount = deviceService.disassociateGateway(idList);
        if (successCount == 0) {
            return AjaxResult.error("解除关联");
        }
        return AjaxResult.success();
    }

    @ApiOperation("获取设备连接状态统计")
    @GetMapping("/getConnectStatusStatistics")
    public AjaxResult getConnectStatusStatistics() {
        ConnectStatusStatisticsVo connectStatusStatisticsVo = deviceService.getConnectStatusStatistics();
        return AjaxResult.success(connectStatusStatisticsVo);
    }

    @ApiOperation("获取设备统计")
    @GetMapping("/getDeviceStatistics")
    public AjaxResult getDeviceStatistics() {
        DeviceStatisticsVo connectStatusStatisticsVo = deviceService.getDeviceStatistics();
        return AjaxResult.success(connectStatusStatisticsVo);
    }

    @ApiOperation("获取设备激活状态统计")
    @GetMapping("/getDeviceStatusStatistics")
    public AjaxResult getDeviceStatusStatistics() {
        DeviceStatusStatisticsVo connectStatusStatisticsVo = deviceService.getDeviceStatusStatistics();
        return AjaxResult.success(connectStatusStatisticsVo);
    }


}
