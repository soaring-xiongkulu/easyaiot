package com.basiclab.iot.common.filter;

import cn.hutool.core.util.StrUtil;
import com.basiclab.iot.common.config.SecurityProperties;
import com.basiclab.iot.common.domain.CommonResult;
import com.basiclab.iot.common.domain.LoginUser;
import com.basiclab.iot.common.service.RedisService;
import com.basiclab.iot.common.utils.SecurityFrameworkUtils;
import com.basiclab.iot.common.utils.StringUtils;
import com.basiclab.iot.common.utils.json.JsonUtils;
import com.basiclab.iot.common.utils.servlet.ServletUtils;
import com.basiclab.iot.common.web.core.handler.GlobalExceptionHandler;
import com.basiclab.iot.common.web.core.util.WebFrameworkUtils;
import com.basiclab.iot.system.api.oauth2.OAuth2TokenApi;
import lombok.RequiredArgsConstructor;
import lombok.SneakyThrows;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.web.filter.OncePerRequestFilter;

import javax.annotation.Resource;
import javax.servlet.FilterChain;
import javax.servlet.ServletException;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;
import java.io.IOException;
import java.net.URLDecoder;
import java.nio.charset.StandardCharsets;

/**
 * Token 过滤器，验证 token 的有效性
 * 验证通过后，获得 {@link LoginUser} 信息，并加入到 Spring Security 上下文
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@RequiredArgsConstructor
@Slf4j
public class TokenAuthenticationFilter extends OncePerRequestFilter {

    private final SecurityProperties securityProperties;

    private final GlobalExceptionHandler globalExceptionHandler;

    private final OAuth2TokenApi oauth2TokenApi;

    @Resource
    private StringRedisTemplate stringRedisTemplate;

    @Override
    @SuppressWarnings("NullableProblems")
    protected void doFilterInternal(HttpServletRequest request, HttpServletResponse response, FilterChain chain)
            throws ServletException, IOException {
        // 情况一，基于 header[login-user] 获得用户，例如说来自 Gateway 或者其它服务透传
        LoginUser loginUser = buildLoginUserByHeader(request);

        // 情况二，基于 Token 获得用户
        // 注意，这里主要满足直接使用 Nginx 直接转发到 Spring Cloud 服务的场景。
        if (loginUser == null) {
            String token = SecurityFrameworkUtils.obtainAuthorization(request,
                    securityProperties.getTokenHeader(), securityProperties.getTokenParameter());
            if (StrUtil.isNotEmpty(token)) {
                Integer userType = WebFrameworkUtils.getLoginUserType(request);
                try {
                    // 1.1 基于 token 构建登录用户
                    loginUser = buildLoginUserByToken(token, userType);
                    // 1.2 模拟 Login 功能，方便日常开发调试
                    if (loginUser == null) {
                        loginUser = mockLoginUser(request, token, userType);
                    }
                } catch (Throwable ex) {
                    CommonResult<?> result = globalExceptionHandler.allExceptionHandler(request, ex);
                    ServletUtils.writeJSON(response, result);
                    return;
                }
            }
        }

        // 设置当前用户
        if (loginUser != null && loginUser.getId() != null) {
            SecurityFrameworkUtils.setLoginUser(loginUser, request);
        }
        // 继续过滤链
        chain.doFilter(request, response);
    }

    private LoginUser buildLoginUserByToken(String token, Integer userType) {
        if (StringUtils.isNotEmpty(token)) {
            LoginUser loginUser = new LoginUser();
            OAuth2AccessTokenDO authDO = this.get(token);
            loginUser.setId(authDO.getUserId());
            loginUser.setUserType(authDO.getUserType());
            loginUser.setTenantId(authDO.getTenantId());
            loginUser.setInfo(authDO.getUserInfo());
            loginUser.setScopes(authDO.getScopes());
            return loginUser;
        }
        return null;
    }

    public OAuth2AccessTokenDO get(String accessToken) {
        String redisKey = formatKey(accessToken);
        return JsonUtils.parseObject(stringRedisTemplate.opsForValue().get(redisKey), OAuth2AccessTokenDO.class);
    }

    private static String formatKey(String accessToken) {
        return String.format("oauth2_access_token:%s", accessToken);
    }

    /**
     * 模拟登录用户，方便日常开发调试
     * <p>
     * 注意，在线上环境下，一定要关闭该功能！！！
     *
     * @param request  请求
     * @param token    模拟的 token，格式为 {@link SecurityProperties#getMockSecret()} + 用户编号
     * @param userType 用户类型
     * @return 模拟的 LoginUser
     */
    private LoginUser mockLoginUser(HttpServletRequest request, String token, Integer userType) {
        if (!securityProperties.getMockEnable()) {
            return null;
        }
        // 必须以 mockSecret 开头
        if (!token.startsWith(securityProperties.getMockSecret())) {
            return null;
        }
        // 构建模拟用户
        Long userId = Long.valueOf(token.substring(securityProperties.getMockSecret().length()));
        return new LoginUser().setId(userId).setUserType(userType)
                .setTenantId(WebFrameworkUtils.getTenantId(request));
    }

    @SneakyThrows
    private LoginUser buildLoginUserByHeader(HttpServletRequest request) {
        String loginUserStr = request.getHeader(SecurityFrameworkUtils.LOGIN_USER_HEADER);
        if (StrUtil.isEmpty(loginUserStr)) {
            return null;
        }
        try {
            loginUserStr = URLDecoder.decode(loginUserStr, StandardCharsets.UTF_8.name()); // 解码，解决中文乱码问题
            return JsonUtils.parseObject(loginUserStr, LoginUser.class);
        } catch (Exception ex) {
            log.error("[buildLoginUserByHeader][解析 LoginUser({}) 发生异常]", loginUserStr, ex);
            ;
            throw ex;
        }
    }

}
