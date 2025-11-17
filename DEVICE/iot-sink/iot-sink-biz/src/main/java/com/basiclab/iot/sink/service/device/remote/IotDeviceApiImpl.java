package com.basiclab.iot.sink.service.device.remote;

import cn.hutool.core.lang.Assert;
import com.basiclab.iot.common.domain.CommonResult;
import com.basiclab.iot.sink.biz.IotDeviceCommonApi;
import com.basiclab.iot.sink.biz.dto.IotDeviceAuthReqDTO;
import com.basiclab.iot.sink.biz.dto.IotDeviceGetReqDTO;
import com.basiclab.iot.sink.biz.dto.IotDeviceRespDTO;
import com.basiclab.iot.sink.config.IotGatewayProperties;
import lombok.extern.slf4j.Slf4j;
import org.springframework.boot.web.client.RestTemplateBuilder;
import org.springframework.core.ParameterizedTypeReference;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpMethod;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;

import javax.annotation.PostConstruct;
import javax.annotation.Resource;

import static com.basiclab.iot.common.exception.GlobalErrorStatus.INTERNAL_SERVER_ERROR;

/**
 * Iot 设备信息 Service 实现类：调用远程的 device http 接口，进行设备认证、设备获取等
 *
 * @author 翱翔的雄库鲁
 */
@Service
@Slf4j
public class IotDeviceApiImpl implements IotDeviceCommonApi {

    @Resource
    private IotGatewayProperties gatewayProperties;

    private RestTemplate restTemplate;

    @PostConstruct
    public void init() {
        IotGatewayProperties.RpcProperties rpc = gatewayProperties.getRpc();
        Assert.notNull(rpc, "RPC 配置不能为空，请检查配置文件中的 basiclab.iot.sink.rpc 配置");
        Assert.notNull(rpc.getUrl(), "RPC URL 配置不能为空");
        Assert.notNull(rpc.getReadTimeout(), "RPC 读取超时时间配置不能为空");
        Assert.notNull(rpc.getConnectTimeout(), "RPC 连接超时时间配置不能为空");
        restTemplate = new RestTemplateBuilder()
                .rootUri(rpc.getUrl() + "/rpc-api/iot/device")
                .setReadTimeout(rpc.getReadTimeout())
                .setConnectTimeout(rpc.getConnectTimeout())
                .build();
    }

    @Override
    public CommonResult<Boolean> authDevice(IotDeviceAuthReqDTO authReqDTO) {
        return doPost("/auth", authReqDTO, new ParameterizedTypeReference<CommonResult<Boolean>>() { });
    }

    @Override
    public CommonResult<IotDeviceRespDTO> getDevice(IotDeviceGetReqDTO getReqDTO) {
        return doPost("/get", getReqDTO, new ParameterizedTypeReference<CommonResult<IotDeviceRespDTO>>() { });
    }

    private <T, R> CommonResult<R> doPost(String url, T body,
                                          ParameterizedTypeReference<CommonResult<R>> responseType) {
        try {
            // 请求
            HttpEntity<T> requestEntity = new HttpEntity<>(body);
            ResponseEntity<CommonResult<R>> response = restTemplate.exchange(
                    url, HttpMethod.POST, requestEntity, responseType);
            // 响应
            CommonResult<R> result = response.getBody();
            Assert.notNull(result, "请求结果不能为空");
            return result;
        } catch (Exception e) {
            log.error("[doPost][url({}) body({}) 发生异常]", url, body, e);
            return CommonResult.error(INTERNAL_SERVER_ERROR);
        }
    }

}
