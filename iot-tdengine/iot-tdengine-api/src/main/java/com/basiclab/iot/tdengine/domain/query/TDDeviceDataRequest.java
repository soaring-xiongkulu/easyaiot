package com.basiclab.iot.tdengine.domain.query;

import lombok.Data;
import org.springframework.validation.annotation.Validated;

import javax.validation.constraints.NotNull;
import java.util.List;


/**
 * @author EasyAIoT
 */
@Data
@Validated
public class TDDeviceDataRequest {
    /**
     * 设备标识
     */
    private String deviceIdentification;
    /**
     * 标识列表
     */
    private List<String> identifierList;
    /**
     * 方法类型 properties:属性 service:服务 event:事件
      */
    private String functionType;
    /**
     * 数据库名
     */
    @NotNull(message = "数据库名不能为空")
    private String tdDatabaseName;
    /**
     * 超级表名
     */
    @NotNull(message = "超级表名不能为空")
    private String tdSuperTableName;


}
