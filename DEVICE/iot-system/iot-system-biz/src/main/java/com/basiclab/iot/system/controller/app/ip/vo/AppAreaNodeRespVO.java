package com.basiclab.iot.system.controller.app.ip.vo;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

import java.util.List;

@Schema(description = "用户 App - 地区节点 Response VO")
@Data
public class AppAreaNodeRespVO {

    @Schema(description = "编号", example = "110000")
    private Integer id;

    @Schema(description = "名字", example = "北京")
    private String name;

    /**
 * AppAreaNodeRespVO
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */

private List<AppAreaNodeRespVO> children;

}
