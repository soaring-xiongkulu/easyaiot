package com.basiclab.iot.system.controller.admin.logger.vo.operatelog;

import com.basiclab.iot.system.dal.dataobject.user.AdminUserDO;
import com.alibaba.excel.annotation.ExcelIgnoreUnannotated;
import com.alibaba.excel.annotation.ExcelProperty;
import com.fhs.core.trans.anno.Trans;
import com.fhs.core.trans.constant.TransType;
import com.fhs.core.trans.vo.VO;
import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

import javax.validation.constraints.NotEmpty;
import java.time.LocalDateTime;

/**
 * OperateLogRespVO
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Schema(description = "管理后台 - 操作日志 Response VO")
@Data
@ExcelIgnoreUnannotated
public class OperateLogRespVO implements VO {

    @Schema(description = "日志编号", example = "1024")
    @ExcelProperty("日志编号")
    private Long id;

    @Schema(description = "链路追踪编号", example = "89aca178-a370-411c-ae02-3f0d672be4ab")
    private String traceId;

    @Schema(description = "用户编号", example = "1024")
    @Trans(type = TransType.SIMPLE, target = AdminUserDO.class, fields = "nickname", ref = "userName")
    private Long userId;
    @Schema(description = "用户昵称", example = "BasicLab")
    @ExcelProperty("操作人")
    private String userName;

    @Schema(description = "操作模块类型", example = "订单")
    @ExcelProperty("操作模块类型")
    private String type;

    @Schema(description = "操作名", example = "创建订单")
    @ExcelProperty("操作名")
    private String subType;

    @Schema(description = "操作模块业务编号", example = "1")
    @ExcelProperty("操作模块业务编号")
    private Long bizId;

    @Schema(description = "操作明细", example = "修改编号为 1 的用户信息，将性别从男改成女，将姓名从BasicLab改成源码。")
    private String action;

    @Schema(description = "拓展字段", example = "{'orderId': 1}")
    private String extra;

    @Schema(description = "请求方法名", example = "GET")
    @NotEmpty(message = "请求方法名不能为空")
    private String requestMethod;

    @Schema(description = "请求地址", example = "/xxx/yyy")
    private String requestUrl;

    @Schema(description = "用户 IP", example = "127.0.0.1")
    private String userIp;

    @Schema(description = "浏览器 UserAgent", example = "Mozilla/5.0")
    private String userAgent;

    @Schema(description = "创建时间")
    private LocalDateTime createTime;

}
