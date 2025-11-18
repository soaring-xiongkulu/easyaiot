package com.basiclab.iot.system.controller.admin.user.vo.profile;

import com.basiclab.iot.system.controller.admin.dept.vo.dept.DeptSimpleRespVO;
import com.basiclab.iot.system.controller.admin.dept.vo.post.PostSimpleRespVO;
import com.basiclab.iot.system.controller.admin.permission.vo.role.RoleSimpleRespVO;
import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

import java.time.LocalDateTime;
import java.util.List;

@Data
@Schema(description = "管理后台 - 用户个人中心信息 Response VO")
public class UserProfileRespVO {

    @Schema(description = "用户编号", example = "1")
    private Long id;

    @Schema(description = "用户账号", example = "Yudao")
    private String username;

    @Schema(description = "用户昵称", example = "BasicLab")
    private String nickname;

    @Schema(description = "用户邮箱", example = "Yudao@iocoder.cn")
    private String email;

    @Schema(description = "手机号码", example = "15601691300")
    private String mobile;

    @Schema(description = "用户性别，参见 SexEnum 枚举类", example = "1")
    private Integer sex;

    @Schema(description = "用户头像", example = "https://www.iocoder.cn/xxx.png")
    private String avatar;

    @Schema(description = "最后登录 IP", example = "192.168.1.1")
    private String loginIp;

    @Schema(description = "最后登录时间", example = "时间戳格式")
    private LocalDateTime loginDate;

    @Schema(description = "创建时间", example = "时间戳格式")
    private LocalDateTime createTime;

    /**
 * UserProfileRespVO
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */

private List<RoleSimpleRespVO> roles;
    /**
     * 所在部门
     */
    private DeptSimpleRespVO dept;
    /**
     * 所属岗位数组
     */
    private List<PostSimpleRespVO> posts;
    /**
     * 社交用户数组
     */
    private List<SocialUser> socialUsers;

    @Schema(description = "社交用户")
    @Data
    public static class SocialUser {

        @Schema(description = "社交平台的类型，参见 SocialTypeEnum 枚举类", example = "10")
        private Integer type;

        @Schema(description = "社交用户的 openid", example = "IPRmJ0wvBptiPIlGEZiPewGwiEiE")
        private String openid;

    }

}
