package com.basiclab.iot.common.utils;

import com.basiclab.iot.common.constant.HeaderConstants;
import org.apache.commons.lang3.StringUtils;
import org.springframework.web.context.request.RequestAttributes;
import org.springframework.web.context.request.RequestContextHolder;
import org.springframework.web.context.request.ServletRequestAttributes;

import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;

/**
 * 登录工具
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
public class LoginUtils {

    public static HttpServletRequest getRequest() {
        RequestAttributes ra = RequestContextHolder.getRequestAttributes();
        ServletRequestAttributes sra = (ServletRequestAttributes) ra;
        return sra.getRequest();
    }

    public static HttpServletResponse getResponse() {
        RequestAttributes ra = RequestContextHolder.getRequestAttributes();
        ServletRequestAttributes sra = (ServletRequestAttributes) ra;
        return sra.getResponse();
    }

    public static String getAppToken() {
        HttpServletRequest request = getRequest();
        return request.getHeader(HeaderConstants.APP_TOKEN);
    }

    public static Long getAppUserId() {
        HttpServletRequest request = getRequest();
        return Long.parseLong(request.getHeader(HeaderConstants.APP_USERID));
    }

//    public static String getAppPhone() {
//        HttpServletRequest request = getRequest();
//        return request.getHeader(HeaderConstants.APP_PHONE);
//    }

    public static String getAppAgent() {
        HttpServletRequest request = getRequest();
        String header = request.getHeader(HeaderConstants.APP_AGENT);
//        return StringUtils.isEmpty(header) ? "IOS" : header;
        return header;
    }

    public static String getAppLang() {
        HttpServletRequest request = getRequest();
        String header = request.getHeader(HeaderConstants.APP_LANG);
        return StringUtils.isEmpty(header) ? "zh_CN" : header;
    }

    public static String getAppNickName() {
        HttpServletRequest request = getRequest();
        return request.getHeader(HeaderConstants.APP_NICKNAME);
    }

    public static Long getAdminUserId() {
        HttpServletRequest request = getRequest();
        String userId = request.getHeader(HeaderConstants.ADMIN_USERID);
        return StringUtils.isEmpty(userId) ? null : Long.parseLong(userId);
    }

    public static String getAdminUsername() {
        HttpServletRequest request = getRequest();
        return request.getHeader(HeaderConstants.ADMIN_USERNAME);
    }

    public static String getDeviceIdentification() {
        HttpServletRequest request = getRequest();
        return request.getHeader(HeaderConstants.DEVICE_IDENTIFICATION);
    }

    public static Long getDeviceId() {
        HttpServletRequest request = getRequest();
        return Long.parseLong(request.getHeader(HeaderConstants.DEVICEID));
    }

}
