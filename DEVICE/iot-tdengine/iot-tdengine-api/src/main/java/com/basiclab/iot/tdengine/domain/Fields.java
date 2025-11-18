package com.basiclab.iot.tdengine.domain;

import com.basiclab.iot.device.enums.device.DataTypeEnum;
import lombok.Data;

import java.io.Serializable;

/**
 * Fields
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Data
public class Fields implements Serializable {

    private static final long serialVersionUID = -1L;

    /**
     * 字段名称
     */
    private String fieldName;

    /**
     * 字段值
     */
    private Object fieldValue;

    /**
     * 字段数据类型
     */
    private DataTypeEnum dataType;

    /**
     * 字段字节大小
     */
    private Integer size;

    public Fields() {
    }

    public Fields(String fieldName) {
        this.fieldName = fieldName;
    }

    public Fields(String fieldName, DataTypeEnum dataType) {
        this.fieldName = fieldName;
        this.dataType = dataType;
    }

    public Fields(String fieldName, DataTypeEnum dataType, Integer size) {
        this.fieldName = fieldName;
        this.dataType = dataType;
        this.size = size;
    }

    public Fields(String fieldName, Object fieldValue, DataTypeEnum dataType, Integer size) {
        this.fieldName = fieldName;
        this.fieldValue = fieldValue;
        this.dataType = dataType;
        this.size = size;
    }
}
