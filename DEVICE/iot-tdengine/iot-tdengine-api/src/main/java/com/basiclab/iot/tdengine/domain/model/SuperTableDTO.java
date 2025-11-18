package com.basiclab.iot.tdengine.domain.model;

import com.basiclab.iot.tdengine.domain.Fields;
import lombok.Builder;
import lombok.Data;

import java.io.Serializable;
import java.util.List;

/**
 * SuperTableDTO
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Data
@Builder
public class SuperTableDTO implements Serializable {

    private static final long serialVersionUID = -1L;

    private List<Fields> schemaFields;

    /**
     * 超级表的标签字段，可以作为子表在超级表里的标识 字符相关数据类型必须指定大小 字段名称和字段数据类型不能为空
     */
    private List<Fields> tagsFields;

    /**
     * 字段信息对象，超级表添加列时使用该属性
     */
    private Fields fields;

    /**
     * 数据库名称
     */
    private String dataBaseName;

    /**
     * 超级表名称
     */
    private String superTableName;

    public SuperTableDTO() {

    }

    public SuperTableDTO(List<Fields> schemaFields, List<Fields> tagsFields, Fields fields, String dataBaseName, String superTableName) {
        this.schemaFields = schemaFields;
        this.tagsFields = tagsFields;
        this.fields = fields;
        this.dataBaseName = dataBaseName;
        this.superTableName = superTableName;
    }
}
