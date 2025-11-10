package com.basiclab.iot.device;

import com.basiclab.iot.common.constant.ServiceNameConstants;
import com.basiclab.iot.common.domain.AjaxResult;
import com.basiclab.iot.common.domain.R;
import com.basiclab.iot.device.domain.device.vo.Device;
import com.basiclab.iot.device.factory.RemoteDeviceFallbackFactory;
import io.swagger.annotations.ApiOperation;
import org.springframework.cloud.openfeign.FeignClient;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;

/**
 * 设备管理服务
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@FeignClient(contextId = "remoteDeviceService", value = ServiceNameConstants.IOT_DEVICE, fallbackFactory = RemoteDeviceFallbackFactory.class)
public interface RemoteDeviceService {

    /**
     * 更新设备在线状态
     *
     * @param device
     * @return
     */
    @PutMapping("/device/updateConnectStatusByClientId")
    public R updateConnectStatusByClientId(@RequestBody Device device);


    /**
     * 客户端身份认证
     *
     * @param params
     * @return
     */
    @PostMapping("/device/clientAuthentication")
    public R<Boolean> clientAuthentication(@RequestBody Map<String, Object> params);

    /**
     * 查询产品下的设备标识
     *
     * @param productIdentification
     * @return
     */
    @GetMapping("/device/selectByProductIdentification/{productIdentification}")
    public AjaxResult selectByProductIdentification(@PathVariable("productIdentification") String productIdentification);


    /**
     * 查询产品下的设备标识
     *
     * @param productIdentification
     * @return
     */
    @GetMapping("/device/selectByProductIdentificationAndDeviceIdentification/{productIdentification}/{deviceIdentification}")
    public R<Device> selectByProductIdentificationAndDeviceIdentification(@PathVariable("productIdentification") String productIdentification,
                                                                          @PathVariable("deviceIdentification") String deviceIdentification);

    /**
     * 根据客户端标识获取设备信息
     *
     * @param clientId
     * @return
     */
    @PostMapping("/device/findOneByClientId")
    public R<Device> findOneByClientId(String clientId);

    /**
     * 根据产品标识获取产品所有关联设备
     *
     * @param productIdentification
     * @return
     */
    @GetMapping("/device/selectAllByProductIdentification/{productIdentification}")
    public R<?> selectAllByProductIdentification(@PathVariable("productIdentification") String productIdentification);

    @PostMapping("/device/selectDeviceByDeviceIdentificationList")
    public R<?> selectDeviceByDeviceIdentificationList(@RequestBody List<String> deviceIdentificationList);

    /**
     * 通过设备标识查询设备
     *
     * @param deviceIdentification
     * @return
     */
    @ApiOperation("通过设备标识查询设备")
    @GetMapping(value = "/findOneByDeviceIdentification/{deviceIdentification}")
    public AjaxResult findOneByDeviceIdentification(@PathVariable("deviceIdentification") String deviceIdentification);
}
