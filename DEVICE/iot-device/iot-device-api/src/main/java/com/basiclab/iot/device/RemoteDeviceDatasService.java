package com.basiclab.iot.device;

import com.basiclab.iot.common.constant.ServiceNameConstants;
import com.basiclab.iot.common.domain.R;
import com.basiclab.iot.device.domain.device.vo.DeviceServiceRecord;
import com.basiclab.iot.device.factory.RemoteDeviceDatasFallbackFactory;
import org.springframework.cloud.openfeign.FeignClient;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;

/**
 * 设备消息服务
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@FeignClient(contextId = "remoteDeviceDatasService", value = ServiceNameConstants.IOT_DEVICE, fallbackFactory = RemoteDeviceDatasFallbackFactory.class)
public interface RemoteDeviceDatasService {

    /**
     * 新增设备消息
     */
    @PostMapping("/device/datas/add")
    public R add(@RequestBody DeviceServiceRecord mqttsDeviceServiceRecord);

}
