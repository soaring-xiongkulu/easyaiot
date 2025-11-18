package com.basiclab.iot.system.framework.operatelog.core;

import cn.hutool.core.convert.Convert;
import cn.hutool.core.util.StrUtil;
import com.basiclab.iot.system.dal.dataobject.user.AdminUserDO;
import com.basiclab.iot.system.service.user.AdminUserService;
import com.mzt.logapi.service.IParseFunction;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Component;

import javax.annotation.Resource;

/**
 * AdminUserParseFunction
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Slf4j
@Component
public class AdminUserParseFunction implements IParseFunction {

    public static final String NAME = "getAdminUserById";

    @Resource
    private AdminUserService adminUserService;

    @Override
    public String functionName() {
        return NAME;
    }

    @Override
    public String apply(Object value) {
        if (StrUtil.isEmptyIfStr(value)) {
            return "";
        }

        // 获取用户信息
        AdminUserDO user = adminUserService.getUser(Convert.toLong(value));
        if (user == null) {
            log.warn("[apply][获取用户{{}}为空", value);
            return "";
        }
        // 返回格式 BasicLab源码(13888888888)
        String nickname = user.getNickname();
        if (StrUtil.isEmpty(user.getMobile())) {
            return nickname;
        }
        return StrUtil.format("{}({})", nickname, user.getMobile());
    }

}
