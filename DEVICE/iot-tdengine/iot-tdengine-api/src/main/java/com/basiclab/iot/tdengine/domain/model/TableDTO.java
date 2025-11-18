package com.basiclab.iot.tdengine.domain.model;

import com.basiclab.iot.tdengine.domain.Fields;
import lombok.Data;

import java.io.Serializable;
import java.util.List;

/**
 * TableDTO
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */

@Data
public class TableDTO implements Serializable {

    private static final long serialVersionUID = -1L;

    private List<Fields> schemaFieldValues;

    /**
     * 超级表标签字段的值 值需要与创建超级表时标签字段的数据类型对应上
     */
    private List<Fields> tagsFieldValues;

    /**
     * 子表名称
     */
    private String tableName;

    /**
     * 数据库名称
     */
    private String dataBaseName;

    /**
     * 超级表名称
     */
    private String superTableName;

    public TableDTO() {

    }

    public TableDTO(List<Fields> schemaFieldValues, List<Fields> tagsFieldValues, String tableName, String dataBaseName, String superTableName) {
        this.schemaFieldValues = schemaFieldValues;
        this.tagsFieldValues = tagsFieldValues;
        this.tableName = tableName;
        this.dataBaseName = dataBaseName;
        this.superTableName = superTableName;
    }
}
