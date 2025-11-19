package com.basiclab.iot.message.domain.model.bean;

import lombok.Data;

import java.io.Serializable;

/**
 * 用户案例
 */
@Data
public class UserCase implements Serializable {

    private static final long serialVersionUID = 2829237163275443844L;

    private String qrCodeUrl;

    private String title;

    private String desc;

}
