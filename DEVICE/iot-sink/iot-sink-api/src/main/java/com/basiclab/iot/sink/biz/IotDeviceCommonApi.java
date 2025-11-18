package com.basiclab.iot.sink.biz;

import com.basiclab.iot.common.domain.CommonResult;
import com.basiclab.iot.sink.biz.dto.IotDeviceAuthReqDTO;
import com.basiclab.iot.sink.biz.dto.IotDeviceGetReqDTO;
import com.basiclab.iot.sink.biz.dto.IotDeviceRespDTO;

/**
 * IotDeviceCommonApi
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */

public interface IotDeviceCommonApi {

    /**
     * 设备认证
     *
     * @param authReqDTO 认证请求
     * @return 认证结果
     */
    CommonResult<Boolean> authDevice(IotDeviceAuthReqDTO authReqDTO);

    /**
     * 获取设备信息
     *
     * @param infoReqDTO 设备信息请求
     * @return 设备信息
     */
    CommonResult<IotDeviceRespDTO> getDevice(IotDeviceGetReqDTO infoReqDTO);

}
