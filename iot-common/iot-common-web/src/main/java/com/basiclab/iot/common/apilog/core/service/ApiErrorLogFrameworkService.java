package com.basiclab.iot.common.apilog.core.service;

import com.basiclab.iot.infra.api.logger.dto.ApiErrorLogCreateReqDTO;

/**
 * API 错误日志 Framework Service 接口
 *
 * @author 安徽上洲智能科技
 */
public interface ApiErrorLogFrameworkService {

    /**
     * 创建 API 错误日志
     *
     * @param reqDTO API 错误日志
     */
    void createApiErrorLog(ApiErrorLogCreateReqDTO reqDTO);

}
