package com.basiclab.iot.common.domain;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableId;
import com.fasterxml.jackson.annotation.JsonFormat;
import lombok.Data;

import java.io.Serializable;
import java.util.Date;

/**
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 * @desc
 * @created 2025-05-27
 */
@Data
public class BasePo implements Serializable {

    protected static final long serialVersionUID = 1L;

    @TableId(type = IdType.AUTO)
    protected Long id;

    @TableField(value = "created_by")
    protected String createdBy = "1";

    @JsonFormat(pattern = "yyyy-MM-dd HH:mm:ss", timezone = "GMT+8")
    @TableField(value = "created_time")
    protected Date createdTime;

    @TableField(value = "updated_by")
    protected String updatedBy = "1";

    @JsonFormat(pattern = "yyyy-MM-dd HH:mm:ss", timezone = "GMT+8")
    @TableField(value = "updated_time")
    protected Date updatedTime;
}
