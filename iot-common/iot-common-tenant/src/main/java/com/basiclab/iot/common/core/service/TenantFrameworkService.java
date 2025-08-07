package com.basiclab.iot.common.core.service;

import java.util.List;

/**
 * Tenant 框架 Service 接口，定义获取租户信息
 *
 * @author 深圳市深度智核科技有限责任公司
 */
public interface TenantFrameworkService {

    /**
     * 获得所有租户
     *
     * @return 租户编号数组
     */
    List<Long> getTenantIds();

    /**
     * 校验租户是否合法
     *
     * @param id 租户编号
     */
    void validTenant(Long id);

}
