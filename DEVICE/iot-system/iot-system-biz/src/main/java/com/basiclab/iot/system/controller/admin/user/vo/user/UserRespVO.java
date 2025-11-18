package com.basiclab.iot.system.controller.admin.user.vo.user;

import com.basiclab.iot.common.excels.core.annotations.DictFormat;
import com.basiclab.iot.common.excels.core.convert.DictConvert;
import com.basiclab.iot.system.enums.DictTypeConstants;
import com.alibaba.excel.annotation.ExcelIgnoreUnannotated;
import com.alibaba.excel.annotation.ExcelProperty;
import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

import java.time.LocalDateTime;
import java.util.Set;

/**
 * UserRespVO
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Schema(description = "管理后台 - 用户信息 Respon
se VO")
@Data
@ExcelIgnoreUnannotated
public class UserRespVO{

    @Schema(description = "用户编号", example = "1")
    @ExcelProperty("用户编号")
    private Long id;

    @Schema(description = "用户账号", example = "Yudao")
    @ExcelProperty("用户名称")
    private String username;

    @Schema(description = "用户昵称", example = "BasicLab")
    @ExcelProperty("用户昵称")
    private String nickname;

    @Schema(description = "备注", example = "我是一个用户")
    private String remark;

    @Schema(description = "部门ID", example = "我是一个用户")
    private Long deptId;
    @Schema(description = "部门名称", example = "IT 部")
    @ExcelProperty("部门名称")
    private String deptName;

    @Schema(description = "岗位编号数组", example = "1")
    private Set<Long> postIds;

    @Schema(description = "用户邮箱", example = "Yudao@iocoder.cn")
    @ExcelProperty("用户邮箱")
    private String email;

    @Schema(description = "手机号码", example = "15601691300")
    @ExcelProperty("手机号码")
    private String mobile;

    @Schema(description = "用户性别，参见 SexEnum 枚举类", example = "1")
    @ExcelProperty(value = "用户性别", converter = DictConvert.class)
    @DictFormat(DictTypeConstants.USER_SEX)
    private Integer sex;

    @Schema(description = "用户头像", example = "https://www.iocoder.cn/xxx.png")
    private String avatar;

    @Schema(description = "状态，参见 CommonStatusEnum 枚举类", example = "1")
    @ExcelProperty(value = "帐号状态", converter = DictConvert.class)
    @DictFormat(DictTypeConstants.COMMON_STATUS)
    private Integer status;

    @Schema(description = "最后登录 IP", example = "192.168.1.1")
    @ExcelProperty("最后登录IP")
    private String loginIp;

    @Schema(description = "最后登录时间", example = "时间戳格式")
    @ExcelProperty("最后登录时间")
    private LocalDateTime loginDate;

    @Schema(description = "创建时间", example = "时间戳格式")
    private LocalDateTime createTime;

}
