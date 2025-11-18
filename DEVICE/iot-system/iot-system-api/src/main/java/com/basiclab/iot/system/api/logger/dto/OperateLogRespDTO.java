package com.basiclab.iot.system.api.logger.dto;

import com.fhs.core.trans.anno.Trans;
import com.fhs.core.trans.constant.TransType;
import com.fhs.core.trans.vo.VO;
import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

import java.time.LocalDateTime;

/**
 * OperateLogRespDTO
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Schema(name = "RPC 服务 - 系统操作日志 Response DTO")
@Data
public class OperateLogRespDTO implements VO {

    @Schema(description = "日志编号", example = "1024")
    private Long id;

    @Schema(description = "链路追踪编号", example = "89aca178-a370-411c-ae02-3f0d672be4ab")
    private String traceId;
    @Schema(description = "用户编号", example = "666")
    @Trans(type = TransType.RPC, targetClassName = "com.basiclab.iot.system.dal.dataobject.user.AdminUserDO",
            fields = "nickname", ref = "userName")
    private Long userId;
    @Schema(description = "用户名称", example = "BasicLab")
    private String userName;
    @Schema(description = "用户类型，参见 UserTypeEnum 枚举", example = "2")
    private Integer userType;
    @Schema(description = "操作模块类型", example = "订单")
    private String type;
    @Schema(description = "操作名", example = "创建订单")
    private String subType;
    @Schema(description = "操作模块业务编号", example = "188")
    private Long bizId;
    @Schema(description = "操作内容",
            example = "修改编号为 1 的用户信息，将性别从男改成女，将姓名从BasicLab改成源码")
    private String action;
    @Schema(description = "拓展字段", example = "{\"orderId\": \"1\"}")
    private String extra;

    @Schema(description = "请求方法名", example = "GET")
    private String requestMethod;
    @Schema(description = "请求地址", example = "/order/get")
    private String requestUrl;
    @Schema(description = "用户 IP", example = "127.0.0.1")
    private String userIp;
    @Schema(description = "浏览器 UserAgent", example = "Mozilla/5.0")
    private String userAgent;

    @Schema(description = "创建时间")
    private LocalDateTime createTime;

}
