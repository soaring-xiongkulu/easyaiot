package com.basiclab.iot.system.dal.pgsql.sms;

import com.basiclab.iot.common.core.mapper.BaseMapperX;
import com.basiclab.iot.common.core.query.QueryWrapperX;
import com.basiclab.iot.system.dal.dataobject.sms.SmsCodeDO;
import org.apache.ibatis.annotations.Mapper;

/**
 * SmsCodeMapper
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Mapper
public interface SmsCodeMapper extends BaseMapperX<SmsCodeDO> {

    default SmsCodeDO selectLastByMobile(String mobile, String code, Integer scene) {
        return selectOne(new QueryWrapperX<SmsCodeDO>()
                .eq("mobile", mobile)
                .eqIfPresent("scene", scene)
                .eqIfPresent("code", code)
                .orderByDesc("id")
                .limitN(1));
    }

}
