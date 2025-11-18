package com.basiclab.iot.system.dal.dataobject.sms;

import com.basiclab.iot.common.enums.CommonStatusEnum;
import com.basiclab.iot.common.core.dataobject.BaseDO;
import com.basiclab.iot.system.framework.sms.core.enums.SmsChannelEnum;
import com.baomidou.mybatisplus.annotation.KeySequence;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;
import lombok.EqualsAndHashCode;
import lombok.ToString;

/**
 * SmsChannelDO
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@TableName(value = "system_sms_channel", autoResultMap = true)
@KeySequence("system_sms_channel_seq") // 用于 Oracle、PostgreSQL、Kingbase、DB2、H2 数据库的主键自增。如果是 MySQL 等数据库，可不写。
@Data
@EqualsAndHashCode(callSuper = true)
@ToString(callSuper = true)
public class SmsChannelDO extends BaseDO {

    /**
     * 渠道编号
     */
    private Long id;
    /**
     * 短信签名
     */
    private String signature;
    /**
     * 渠道编码
     *
     * 枚举 {@link SmsChannelEnum}
     */
    private String code;
    /**
     * 启用状态
     *
     * 枚举 {@link CommonStatusEnum}
     */
    private Integer status;
    /**
     * 备注
     */
    private String remark;
    /**
     * 短信 API 的账号
     */
    private String apiKey;
    /**
     * 短信 API 的密钥
     */
    private String apiSecret;
    /**
     * 短信发送回调 URL
     */
    private String callbackUrl;

}
