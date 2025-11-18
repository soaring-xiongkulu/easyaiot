package com.basiclab.iot.sink.messagebus.publisher;

import com.basiclab.iot.sink.biz.dto.IotDeviceRespDTO;
import com.basiclab.iot.sink.service.device.DeviceService;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import javax.annotation.Resource;

/**
 * IotDeviceServiceImpl
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */

@Service
@Slf4j
public class IotDeviceServiceImpl implements IotDeviceService {

    @Resource
    private DeviceService deviceService;

    @Override
    public IotDeviceRespDTO getDeviceFromCache(String productIdentification, String deviceIdentification) {
        return deviceService.getDevice(productIdentification, deviceIdentification);
    }

    @Override
    public IotDeviceRespDTO getDeviceFromCache(Long id) {
        return deviceService.getDevice(id);
    }

}