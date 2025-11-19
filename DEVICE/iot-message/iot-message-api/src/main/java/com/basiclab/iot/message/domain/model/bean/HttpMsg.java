package com.basiclab.iot.message.domain.model.bean;

import lombok.Getter;
import lombok.Setter;
import lombok.ToString;

import java.io.Serializable;
import java.net.HttpCookie;
import java.util.List;
import java.util.Map;

/**
 * http消息体
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 * @since 2024-07-17
 */
@Getter
@Setter
@ToString
public class HttpMsg implements Serializable {

    private static final long serialVersionUID = 114436270588113296L;

    private String url;

    private String body;

    private Map<String, Object> paramMap;

    private Map<String, Object> headerMap;

    private List<HttpCookie> cookies;

    private String msgName;

    private String method;

    private boolean httpUseProxy;

    private String bodyType;

}
