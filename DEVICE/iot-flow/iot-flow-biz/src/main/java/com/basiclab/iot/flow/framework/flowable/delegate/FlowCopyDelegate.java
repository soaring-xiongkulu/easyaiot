package com.basiclab.iot.flow.framework.flowable.delegate;

import com.basiclab.iot.flow.dal.dataobject.FlowProcessInstanceCopyDO;
import com.basiclab.iot.flow.dal.pgsql.FlowProcessInstanceCopyMapper;
import com.basiclab.iot.flow.framework.flowable.core.SimpleModelConverter;
import com.basiclab.iot.flow.framework.flowable.core.TaskCandidateConf;
import com.basiclab.iot.flow.service.candidate.FlowCandidateService;
import lombok.extern.slf4j.Slf4j;
import org.flowable.bpmn.model.BpmnModel;
import org.flowable.bpmn.model.ExtensionElement;
import org.flowable.bpmn.model.FlowElement;
import org.flowable.bpmn.model.ServiceTask;
import org.flowable.engine.RepositoryService;
import org.flowable.engine.delegate.DelegateExecution;
import org.springframework.context.ApplicationContext;
import org.springframework.stereotype.Component;

import java.util.List;

/**
 * 抄送节点委托：按扩展元素 candidateConf 解析抄送目标，写 flow_copy。
 * BPMN 表达式：${flowCopyDelegate.apply(execution, '&lt;nodeId&gt;')}
 */
@Slf4j
@Component
public class FlowCopyDelegate {

    private final ApplicationContext applicationContext;

    public FlowCopyDelegate(ApplicationContext applicationContext) {
        this.applicationContext = applicationContext;
    }

    public void apply(DelegateExecution execution, String nodeId) {
        try {
            doApply(execution, nodeId);
        }
        catch (Exception e) {
            // 抄送失败不阻断主流程
            log.error("[apply] 抄送节点执行失败, instanceId={}, nodeId={}", execution.getProcessInstanceId(), nodeId, e);
        }
    }

    private void doApply(DelegateExecution execution, String nodeId) {
        TaskCandidateConf conf = loadConf(execution, nodeId);
        Long startUserId = toLong(execution.getVariable(SimpleModelConverter.START_USER_VAR));
        List<Long> userIds = candidateService().resolve(conf, startUserId, execution.getVariables(), nodeId);
        if (userIds.isEmpty()) {
            log.info("[apply] 抄送目标为空，跳过, instanceId={}, nodeId={}", execution.getProcessInstanceId(), nodeId);
            return;
        }
        RepositoryService repositoryService = bean(RepositoryService.class);
        var definition = repositoryService.getProcessDefinition(execution.getProcessDefinitionId());

        FlowProcessInstanceCopyDO proto = new FlowProcessInstanceCopyDO();
        proto.setProcessInstanceId(execution.getProcessInstanceId());
        proto.setProcessInstanceName((String) execution.getVariable("PROCESS_INSTANCE_NAME"));
        proto.setCategory(definition.getCategory());
        proto.setActivityId(nodeId);
        proto.setStartUserId(startUserId);
        FlowElement element = repositoryService.getBpmnModel(execution.getProcessDefinitionId()).getFlowElement(nodeId);
        proto.setTaskName(element == null ? null : element.getName());

        FlowProcessInstanceCopyMapper mapper = bean(FlowProcessInstanceCopyMapper.class);
        for (Long userId : userIds) {
            FlowProcessInstanceCopyDO copy = new FlowProcessInstanceCopyDO();
            copy.setProcessInstanceId(proto.getProcessInstanceId());
            copy.setProcessInstanceName(proto.getProcessInstanceName());
            copy.setCategory(proto.getCategory());
            copy.setActivityId(proto.getActivityId());
            copy.setTaskName(proto.getTaskName());
            copy.setStartUserId(proto.getStartUserId());
            copy.setUserId(userId);
            copy.setReason("抄送节点");
            mapper.insert(copy);
        }
        log.info("[apply] 抄送完成, instanceId={}, nodeId={}, targets={}",
                execution.getProcessInstanceId(), nodeId, userIds);
    }

    private TaskCandidateConf loadConf(DelegateExecution execution, String nodeId) {
        try {
            FlowElement element = bean(RepositoryService.class)
                    .getBpmnModel(execution.getProcessDefinitionId()).getFlowElement(nodeId);
            if (element instanceof ServiceTask serviceTask) {
                List<ExtensionElement> exts = serviceTask.getExtensionElements()
                        .get(SimpleModelConverter.EXT_CANDIDATE_CONF);
                return TaskCandidateConf.parse(exts == null || exts.isEmpty() ? null : exts.get(0));
            }
        }
        catch (Exception e) {
            log.warn("[loadConf] 抄送配置读取失败, nodeId={}", nodeId, e);
        }
        return null;
    }

    private FlowCandidateService candidateService() {
        return applicationContext.getBean(FlowCandidateService.class);
    }

    private <T> T bean(Class<T> clazz) {
        return applicationContext.getBean(clazz);
    }

    private Long toLong(Object value) {
        if (value instanceof Number number) {
            return number.longValue();
        }
        return null;
    }

}
