package com.basiclab.iot.file.domain.qo;

import com.basiclab.iot.common.domain.PageQo;
import io.swagger.annotations.ApiModel;
import io.swagger.annotations.ApiModelProperty;
import lombok.Data;

import java.io.Serializable;

/**
 * SysFileQo
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Data
@ApiModel(value = "SysFileQo对象", description = "文件管理Qo")
public class SysFileQo extends PageQo implements Serializable {

    private static final long serialVersionUID = 319717507762690848L;
    @ApiModelProperty(value = "桶名称")
    String bucketName;
    @ApiModelProperty(value = "对象名称")
    String objectName;
    @ApiModelProperty(value = "文件名称")
    String fileName;
    @ApiModelProperty(value = "前缀")
    String prefix;
    @ApiModelProperty(value = "文件路径")
    String path;
    @ApiModelProperty(value = "匹配条件")
    String key;
}
