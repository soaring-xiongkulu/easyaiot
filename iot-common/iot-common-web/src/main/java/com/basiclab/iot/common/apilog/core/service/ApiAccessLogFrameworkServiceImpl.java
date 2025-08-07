package com.basiclab.iot.common.apilog.core.service;

import com.basiclab.iot.infra.api.logger.ApiAccessLogApi;
import com.basiclab.iot.infra.api.logger.dto.ApiAccessLogCreateReqDTO;
import lombok.RequiredArgsConstructor;

/**
 * API 访问日志 Framework Service 实现类
 *
 * 基于 {@link ApiAccessLogApi} 服务，记录访问日志
 *
 * @author 安徽上洲智能科技
 */
@RequiredArgsConstructor
public class ApiAccessLogFrameworkServiceImpl implements ApiAccessLogFrameworkService {

    private final ApiAccessLogApi apiAccessLogApi;

    @Override
    public void createApiAccessLog(ApiAccessLogCreateReqDTO reqDTO) {
        apiAccessLogApi.createApiAccessLog(reqDTO);
    }

}
