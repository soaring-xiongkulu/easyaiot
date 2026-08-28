package com.basiclab.iot.flow.controller.admin.alertrecord;

import com.basiclab.iot.common.domain.CommonResult;
import com.basiclab.iot.common.domain.PageParam;
import com.basiclab.iot.common.domain.PageResult;
import com.basiclab.iot.common.utils.json.JsonUtils;
import com.basiclab.iot.common.utils.SecurityFrameworkUtils;
import com.basiclab.iot.flow.dal.dataobject.FlowAlertRecordDO;
import com.basiclab.iot.flow.service.alertrecord.FlowAlertRecordService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.media.Schema;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.Data;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import javax.annotation.Resource;
import javax.validation.Valid;
import javax.validation.constraints.NotEmpty;
import javax.validation.constraints.NotNull;
import java.io.Serializable;
import java.time.LocalDateTime;
import java.util.List;
import java.util.Map;

import static com.basiclab.iot.common.domain.CommonResult.success;

@Tag(name = "管理后台 - FLOW 告警处理记录")
@RestController
@RequestMapping("/flow/alert-record")
@Validated
public class FlowAlertRecordController {

    @Resource
    private FlowAlertRecordService alertRecordService;

    @GetMapping("/page")
    @Operation(summary = "告警处理记录分页")
    public CommonResult<PageResult<RecordVO>> getAlertRecordPage(@Validated PageParam pageParam,
                                                                 @RequestParam(value = "alertId", required = false) Long alertId,
                                                                 @RequestParam(value = "alertSource", required = false) String alertSource,
                                                                 @RequestParam(value = "processInstanceStatus", required = false) Integer processInstanceStatus) {
        PageResult<FlowAlertRecordDO> page = alertRecordService.getAlertRecordPage(pageParam,
                alertId, alertSource, processInstanceStatus);
        return success(new PageResult<>(page.getList().stream().map(RecordVO::of).toList(), page.getTotal()));
    }

    @GetMapping("/my-page")
    @Operation(summary = "我负责的告警处理记录分页")
    public CommonResult<PageResult<RecordVO>> getMyAlertRecordPage(@Validated PageParam pageParam,
                                                                   @RequestParam(value = "alertId", required = false) Long alertId,
                                                                   @RequestParam(value = "alertSource", required = false) String alertSource,
                                                                   @RequestParam(value = "processInstanceStatus", required = false) Integer processInstanceStatus) {
        PageResult<FlowAlertRecordDO> page = alertRecordService.getMyAlertRecordPage(
                SecurityFrameworkUtils.getLoginUserId(), pageParam, alertId, alertSource, processInstanceStatus);
        return success(new PageResult<>(page.getList().stream().map(RecordVO::of).toList(), page.getTotal()));
    }

    @GetMapping("/list-by-alert-ids")
    @Operation(summary = "按告警 ID 批量查询处理状态")
    @Parameter(name = "alertIds", description = "告警编号（逗号分隔）", required = true)
    public CommonResult<List<RecordVO>> getAlertRecordListByAlertIds(@RequestParam("alertIds") String alertIds) {
        List<Long> ids = java.util.Arrays.stream(alertIds.split(","))
                .map(String::trim).filter(s -> s.matches("\\d+")).map(Long::valueOf).toList();
        return success(alertRecordService.getAlertRecordListByAlertIds(ids)
                .stream().map(RecordVO::of).toList());
    }

    @PostMapping("/trigger")
    @Operation(summary = "手动为存量告警发起处理流程")
    public CommonResult<RecordVO> triggerAlertRecord(@RequestBody TriggerReq reqVO) {
        FlowAlertRecordDO record = alertRecordService.triggerAlertRecord(reqVO.getAlertId(),
                reqVO.getProcessDefinitionKey());
        return success(RecordVO.of(record));
    }

    @GetMapping("/get")
    @Operation(summary = "告警处理记录详情")
    @Parameter(name = "id", description = "编号", required = true)
    public CommonResult<RecordVO> getAlertRecord(@RequestParam("id") Long id) {
        return success(RecordVO.of(alertRecordService.getAlertRecord(id)));
    }

    @Schema(description = "管理后台 - 告警处理记录 VO")
    @Data
    public static class RecordVO implements Serializable {

        private static final long serialVersionUID = 1L;

        private Long id;
        private Long alertId;
        private String alertSource;
        /** 告警快照（JSON 对象） */
        private Map<String, Object> alertSnapshot;
        private String processInstanceId;
        private String processDefinitionKey;
        /** 1 处理中 / 2 已处理(通过) / 3 已关闭(拒绝) / 4 已取消 */
        private Integer processInstanceStatus;
        private String currentTaskName;
        private String currentAssignees;
        private LocalDateTime finishTime;
        private LocalDateTime createTime;

        public static RecordVO of(FlowAlertRecordDO record) {
            if (record == null) {
                return null;
            }
            RecordVO vo = new RecordVO();
            vo.setId(record.getId());
            vo.setAlertId(record.getAlertId());
            vo.setAlertSource(record.getAlertSource());
            vo.setAlertSnapshot(parseSnapshot(record.getAlertSnapshot()));
            vo.setProcessInstanceId(record.getProcessInstanceId());
            vo.setProcessDefinitionKey(record.getProcessDefinitionKey());
            vo.setProcessInstanceStatus(record.getProcessInstanceStatus());
            vo.setCurrentTaskName(record.getCurrentTaskName());
            vo.setCurrentAssignees(record.getCurrentAssignees());
            vo.setFinishTime(record.getFinishTime());
            vo.setCreateTime(record.getCreateTime());
            return vo;
        }

        private static Map<String, Object> parseSnapshot(String snapshot) {
            if (snapshot == null || snapshot.isEmpty()) {
                return null;
            }
            try {
                return JsonUtils.parseObject(snapshot, Map.class);
            }
            catch (Exception e) {
                return null;
            }
        }

    }

    @Schema(description = "手动触发 Request VO")
    @Data
    public static class TriggerReq implements Serializable {

        private static final long serialVersionUID = 1L;

        @NotNull(message = "告警编号不能为空")
        private Long alertId;
        @NotEmpty(message = "流程标识不能为空")
        private String processDefinitionKey;

    }

}
