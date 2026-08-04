package com.basiclab.iot.infra.service.platformbranding;

import cn.hutool.core.util.StrUtil;
import com.basiclab.iot.infra.dal.dataobject.file.FileDO;

/**
 * 构造品牌图片的同源公开访问地址。
 *
 * <p>品牌配置不能直接返回 {@link FileDO#getUrl()}，因为该地址包含文件存储配置中的环境域名，
 * 在容器或反向代理部署后可能是浏览器无法访问的内部地址。公开地址不携带原文件扩展名，
 * 避免被历史 Nginx 静态资源正则当作本地文件处理。</p>
 */
public final class PlatformBrandingFileUrlBuilder {

    private PlatformBrandingFileUrlBuilder() {
    }

    public static String build(FileDO file) {
        return StrUtil.format("/admin-api/infra/platform-branding/image/view?fileId={}", file.getId());
    }
}
