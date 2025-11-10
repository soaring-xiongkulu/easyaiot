package com.basiclab.iot.system.service.member;

/**
 * Member Service 接口
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
public interface MemberService {

    /**
     * 获得会员用户的手机号码
     *
     * @param id 会员用户编号
     * @return 手机号码
     */
    String getMemberUserMobile(Long id);

    /**
     * 获得会员用户的邮箱
     *
     * @param id 会员用户编号
     * @return 邮箱
     */
    String getMemberUserEmail(Long id);

}
