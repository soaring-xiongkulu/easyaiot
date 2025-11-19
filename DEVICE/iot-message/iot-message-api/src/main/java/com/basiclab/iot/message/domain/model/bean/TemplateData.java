package com.basiclab.iot.message.domain.model.bean;

import lombok.Getter;
import lombok.Setter;

import java.io.Serializable;

/**
 * 模板数据
 */
@Getter
@Setter
public class TemplateData implements Serializable {

    private String name;

    private String value;

    private String color;
}
