package com.basiclab.iot.message.domain.model.bean;

import lombok.Getter;
import lombok.Setter;
import lombok.ToString;

import java.io.File;
import java.io.Serializable;
import java.util.List;

/**
 * 邮件消息体
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 * @since 2024-07-17
 */
@Getter
@Setter
@ToString
public class MailMsg implements Serializable {

    private static final long serialVersionUID = 7269816872586216264L;

    /**
     * 标题
     */
    private String mailTitle;

    /**
     * 抄送
     */
    private String mailCc;

    /**
     * 附件
     */
    private List<File> mailFiles;

    /**
     * 内容
     */
    private String mailContent;

    /**
     * 目标用户
     */
    private String previewUser;

}
