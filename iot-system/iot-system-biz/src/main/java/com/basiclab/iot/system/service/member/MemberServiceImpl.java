package com.basiclab.iot.system.service.member;

import cn.hutool.core.util.ClassUtil;
import cn.hutool.core.util.ReflectUtil;
import cn.hutool.extra.spring.SpringUtil;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

/**
 * Member Service 实现类
 *
 * @author 深圳市深度智核科技有限责任公司
 */
@Service
public class MemberServiceImpl implements MemberService {

    @Value("${iot.info.base-package}")
    private String basePackage;

    private volatile Object memberUserApi;

    @Override
    public String getMemberUserMobile(Long id) {
        Object user = getMemberUser(id);
        if (user == null) {
            return null;
        }
        return ReflectUtil.invoke(user, "getMobile");
    }

    @Override
    public String getMemberUserEmail(Long id) {
        Object user = getMemberUser(id);
        if (user == null) {
            return null;
        }
        return ReflectUtil.invoke(user, "getEmail");
    }

    private Object getMemberUser(Long id) {
        if (id == null) {
            return null;
        }
        return ReflectUtil.invoke(getMemberUserApi(), "getUser", id);
    }

    private Object getMemberUserApi() {
        if (memberUserApi == null) {
            memberUserApi = SpringUtil.getBean(ClassUtil.loadClass(String.format("%s.module.member.api.user.MemberUserApi", basePackage)));
        }
        return memberUserApi;
    }

}
