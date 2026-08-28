package com.basiclab.iot.flow.service.notify;

import cn.hutool.core.collection.CollUtil;
import cn.hutool.core.util.StrUtil;
import com.basiclab.iot.flow.enums.FlowEnums;
import com.basiclab.iot.flow.service.candidate.FlowCandidateService;
import com.basiclab.iot.flow.service.instance.FlowProcessInstanceServiceImpl;
import com.basiclab.iot.system.api.notify.NotifyMessageSendApi;
import com.basiclab.iot.system.api.notify.dto.NotifySendSingleToUserReqDTO;
import lombok.extern.slf4j.Slf4j;
import org.flowable.engine.RuntimeService;
import org.springframework.stereotype.Service;

import javax.annotation.Resource;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;

/**
 * FLOW 站内信通知 Service 实现类
 *
 * 通过 Feign 调用 system 服务发送站内信，模板 code = flow_task_todo，
 * 模板参数：processInstanceName / taskName / startUser / deepLink。
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Service
@Slf4j
public class FlowNotifyServiceImpl implements FlowNotifyService {

    /** 站内信模板 code（种子数据见 .scripts/flow/patches/flow_notify_template.sql） */
    public static final String TEMPLATE_CODE_FLOW_TASK_TODO = "flow_task_todo";

    @Resource
    private NotifyMessageSendApi notifyMessageSendApi;
    @Resource
    private RuntimeService runtimeService;
    @Resource
    private FlowCandidateService candidateService;

    @Override
    public void notifyTaskTodo(String processInstanceId, String taskId, String taskName, List<Long> userIds) {
        if (StrUtil.hasBlank(processInstanceId, taskId) || CollUtil.isEmpty(userIds)) {
            return;
        }
        try {
            Map<String, Object> variables = runtimeService.getVariables(processInstanceId);
            Object nameObj = variables.get(FlowProcessInstanceServiceImpl.INSTANCE_NAME_VAR);
            String instanceName = nameObj == null ? null : String.valueOf(nameObj);
            if (instanceName == null) {
                instanceName = "流程" + processInstanceId;
            }
            Long startUserId = parseLong(variables.get(FlowEnums.PROCESS_START_USER_VAR));
            Map<Long, String> nicknameMap = startUserId == null ? Map.of()
                    : candidateService.getUserNicknameMap(Set.of(startUserId));

            Map<String, Object> params = new HashMap<>();
            params.put("processInstanceName", instanceName);
            params.put("taskName", StrUtil.nullToEmpty(taskName));
            params.put("startUser", nicknameMap.getOrDefault(startUserId, "未知"));
            params.put("deepLink", "flow://instance/" + processInstanceId + "?taskId=" + taskId);

            for (Long userId : userIds) {
                if (userId == null) {
                    continue;
                }
                NotifySendSingleToUserReqDTO reqDTO = new NotifySendSingleToUserReqDTO();
                reqDTO.setUserId(userId);
                reqDTO.setTemplateCode(TEMPLATE_CODE_FLOW_TASK_TODO);
                reqDTO.setTemplateParams(params);
                notifyMessageSendApi.sendSingleMessageToAdmin(reqDTO);
            }
            log.info("[notifyTaskTodo] 待办站内信已发送, instance={}, task={}, users={}",
                    processInstanceId, taskId, userIds);
        }
        catch (Exception e) {
            log.warn("[notifyTaskTodo] 待办站内信发送失败(不影响流程), instance={}, task={}",
                    processInstanceId, taskId, e);
        }
    }

    private Long parseLong(Object value) {
        if (value instanceof Number number) {
            return number.longValue();
        }
        if (value instanceof String str && str.matches("\\d+")) {
            return Long.valueOf(str);
        }
        return null;
    }

}
