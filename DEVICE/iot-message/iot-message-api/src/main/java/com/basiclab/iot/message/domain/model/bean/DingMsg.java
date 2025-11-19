package com.basiclab.iot.message.domain.model.bean;

import lombok.Getter;
import lombok.Setter;
import lombok.ToString;

import java.io.Serializable;

/**
 * 钉钉消息体
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 * @since 2024-07-17
 */
@Getter
@Setter
@ToString
public class DingMsg implements Serializable {
    private static final long serialVersionUID = 1L;

    private String content;

    private String title;

    private String picUrl;

    private String url;

    private String btnTxt;

    private String btnUrl;
}
