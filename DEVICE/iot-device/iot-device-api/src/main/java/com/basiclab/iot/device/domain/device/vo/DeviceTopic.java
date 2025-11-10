package com.basiclab.iot.device.domain.device.vo;

import com.baomidou.mybatisplus.annotation.FieldFill;
import com.baomidou.mybatisplus.annotation.TableField;
import io.swagger.annotations.ApiModel;
import io.swagger.annotations.ApiModelProperty;
import lombok.*;
import lombok.experimental.Accessors;
import org.springframework.validation.annotation.Validated;

import javax.validation.constraints.NotNull;
import java.io.Serializable;
import java.time.LocalDateTime;

/**
* @Description: java类作用描述
* @author 翱翔的雄库鲁
* @email andywebjava@163.com
* @wechat EasyAIoT2025
* @E-mail: andywebjava@163.com
* @Website: https://gitee.com/soaring-xiongkulu/easyaiot
* @CreateDate: 2025/6/15 19:35
* @UpdateDate: 2025/6/15 19:35
* @UpdateRemark: 修改内容
* @Version: V1.0
*/
@ApiModel(value="设备Topic数据表")
@Data
@NoArgsConstructor
@AllArgsConstructor
@ToString(callSuper = true)
@Accessors(chain = true)
@Builder
@Validated
public class DeviceTopic implements Serializable {
    /**
    * id
    */
    @ApiModelProperty(value="id")
    private Long id;

    /**
    * 设备标识
    */
    @ApiModelProperty(value="设备标识", required = true)
    @NotNull(message = "设备标识不能为空")
    private String deviceIdentification;

    /**
    * 类型(0:基础Topic,1:自定义Topic)
    */
    @ApiModelProperty(value="类型(0:基础Topic,1:自定义Topic)")
    private String type;

    /**
    * topic
    */
    @ApiModelProperty(value="topic")
    private String topic;

    /**
    * 发布者
    */
    @ApiModelProperty(value="发布者")
    private String publisher;

    /**
    * 订阅者
    */
    @ApiModelProperty(value="订阅者")
    private String subscriber;

    /**
    * 创建者
    */
    @ApiModelProperty(value="创建者")
    @TableField(value = "create_by", fill = FieldFill.INSERT)
    private String createBy;

    /**
    * 创建时间
    */
    @ApiModelProperty(value="创建时间")
    @TableField(value = "create_time", fill = FieldFill.INSERT)
    private LocalDateTime createTime;

    /**
    * 更新者
    */
    @ApiModelProperty(value="更新者")
    @TableField(value = "update_by", fill = FieldFill.INSERT_UPDATE)
    private String updateBy;

    /**
    * 更新时间
    */
    @ApiModelProperty(value="更新时间")
    @TableField(value = "update_time", fill = FieldFill.INSERT_UPDATE)
    private LocalDateTime updateTime;

    /**
    * 备注
    */
    @ApiModelProperty(value="备注")
    private String remark;

    private static final long serialVersionUID = 1L;
}