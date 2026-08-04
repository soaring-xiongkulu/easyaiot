package com.basiclab.iot.infra.service.platformbranding;

import com.basiclab.iot.infra.controller.admin.platformbranding.vo.PlatformBrandingRespVO;
import com.basiclab.iot.infra.controller.admin.platformbranding.vo.PlatformBrandingSaveReqVO;

/**
 * 平台品牌配置 Service
 */
public interface PlatformBrandingService {

    /**
     * 获取全平台品牌配置
     *
     * @return 品牌配置；没有数据库记录时返回空字段
     */
    PlatformBrandingRespVO getPlatformBranding();

    /**
     * 保存全平台品牌配置
     *
     * @param reqVO 完整配置
     * @return 保存后的配置
     */
    PlatformBrandingRespVO savePlatformBranding(PlatformBrandingSaveReqVO reqVO);

    /**
     * 将全平台品牌配置持久化为当前默认状态
     *
     * @return 重置后的配置
     */
    PlatformBrandingRespVO resetPlatformBranding();
}
