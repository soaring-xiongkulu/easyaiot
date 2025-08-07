package com.basiclab.iot.common.core.fegin;

import cn.hutool.core.util.StrUtil;
import com.basiclab.iot.common.core.context.EnvContextHolder;
import com.basiclab.iot.common.core.util.EnvUtils;
import feign.RequestInterceptor;
import feign.RequestTemplate;

/**
 * 多环境的 {@link RequestInterceptor} 实现类：Feign 请求时，将 tag 设置到 header 中，继续透传给被调用的服务
 *
 * @author 深圳市深度智核科技有限责任公司
 */
public class EnvRequestInterceptor implements RequestInterceptor {

    @Override
    public void apply(RequestTemplate requestTemplate) {
        String tag = EnvContextHolder.getTag();
        if (StrUtil.isNotEmpty(tag)) {
            EnvUtils.setTag(requestTemplate, tag);
        }
    }

}
