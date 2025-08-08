package com.basiclab.iot.system.dal.pgsql.sms;

import com.basiclab.iot.common.core.mapper.BaseMapperX;
import com.basiclab.iot.common.core.query.QueryWrapperX;
import com.basiclab.iot.system.dal.dataobject.sms.SmsCodeDO;
import org.apache.ibatis.annotations.Mapper;

@Mapper
public interface SmsCodeMapper extends BaseMapperX<SmsCodeDO> {

    /**
     * 获得手机号的最后一个手机验证码
     *
     * @param mobile 手机号
     * @param scene 发送场景，选填
     * @param code 验证码 选填
     * @return 手机验证码
     */
    default SmsCodeDO selectLastByMobile(String mobile, String code, Integer scene) {
        return selectOne(new QueryWrapperX<SmsCodeDO>()
                .eq("mobile", mobile)
                .eqIfPresent("scene", scene)
                .eqIfPresent("code", code)
                .orderByDesc("id")
                .limitN(1));
    }

}
