package com.basiclab.iot.system.dal.dataobject.mail;

import com.basiclab.iot.common.core.dataobject.BaseDO;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;
import lombok.EqualsAndHashCode;

/**
 * MailAccountDO
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@TableName(value = "system_mail_account", autoResultMap = true)
@Data
@EqualsAndHashCode(callSuper = true)
public class MailAccountDO extends BaseDO {

    /**
     * 主键
     */
    @TableId
    private Long id;
    /**
     * 邮箱
     */
    private String mail;

    /**
     * 用户名
     */
    private String username;
    /**
     * 密码
     */
    private String password;
    /**
     * SMTP 服务器域名
     */
    private String host;
    /**
     * SMTP 服务器端口
     */
    private Integer port;
    /**
     * 是否开启 SSL
     */
    private Boolean sslEnable;
    /**
     * 是否开启 STARTTLS
     */
    private Boolean starttlsEnable;

}
