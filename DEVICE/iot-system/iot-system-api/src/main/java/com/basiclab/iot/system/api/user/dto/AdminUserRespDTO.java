package com.basiclab.iot.system.api.user.dto;

import com.fhs.core.trans.vo.VO;
import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

import java.util.Set;

/**
 * AdminUserRespDTO
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Schema(description = "RPC 服务 - Admin 用户 Response DTO")
@Data
public class AdminUserRespDTO implements VO {

    @Schema(description = "用户 ID", example = "1024")
    private Long id;

    @Schema(description = "用户账号", example = "admin")
    private String username;

    @Schema(description = "用户昵称", example = "小王")
    private String nickname;

    @Schema(description = "帐号状态", example = "1")
    private Integer status;

    @Schema(description = "部门编号", example = "1")
    private Long deptId;

    @Schema(description = "岗位编号数组", example = "[1, 3]")
    private Set<Long> postIds;

    @Schema(description = "手机号码", example = "15601691300")
    private String mobile;

    @Schema(description = "是否在做实验：0-否，1-是", example = "0")
    private Integer doExperiment;

    @Schema(description = "用户积分", example = "10000")
    private Long integral;
}
