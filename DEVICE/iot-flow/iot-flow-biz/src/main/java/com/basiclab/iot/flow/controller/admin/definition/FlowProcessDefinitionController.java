package com.basiclab.iot.flow.controller.admin.definition;

import com.basiclab.iot.common.domain.CommonResult;
import com.basiclab.iot.common.domain.PageParam;
import com.basiclab.iot.common.domain.PageResult;
import com.basiclab.iot.flow.controller.admin.definition.vo.FlowDefinitionRespVO;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.tags.Tag;
import org.flowable.engine.RepositoryService;
import org.flowable.engine.repository.Deployment;
import org.flowable.engine.repository.ProcessDefinition;
import org.flowable.engine.repository.ProcessDefinitionQuery;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import javax.annotation.Resource;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

import static com.basiclab.iot.common.domain.CommonResult.success;

@Tag(name = "管理后台 - FLOW 流程定义")
@RestController
@RequestMapping("/flow/process-definition")
@Validated
public class FlowProcessDefinitionController {

    @Resource
    private RepositoryService repositoryService;

    @GetMapping("/page")
    @Operation(summary = "获得流程定义分页（含历史版本）")
    public CommonResult<PageResult<FlowDefinitionRespVO>> getProcessDefinitionPage(
            @Validated PageParam pageParam,
            @RequestParam(value = "key", required = false) String key,
            @RequestParam(value = "name", required = false) String name,
            @RequestParam(value = "category", required = false) String category) {
        ProcessDefinitionQuery query = repositoryService.createProcessDefinitionQuery();
        if (key != null && !key.isEmpty()) {
            query.processDefinitionKey(key);
        }
        if (name != null && !name.isEmpty()) {
            query.processDefinitionNameLike("%" + name + "%");
        }
        if (category != null && !category.isEmpty()) {
            query.processDefinitionCategory(category);
        }
        query.orderByProcessDefinitionKey().asc().orderByProcessDefinitionVersion().desc();
        long total = query.count();
        List<ProcessDefinition> definitions = query.listPage(
                (pageParam.getPageNo() - 1) * pageParam.getPageSize(), pageParam.getPageSize());
        return success(new PageResult<>(buildList(definitions), total));
    }

    @GetMapping("/list")
    @Operation(summary = "获得流程定义列表（不分页）")
    public CommonResult<List<FlowDefinitionRespVO>> getProcessDefinitionList(
            @RequestParam(value = "key", required = false) String key,
            @RequestParam(value = "name", required = false) String name,
            @RequestParam(value = "suspensionState", required = false) Integer suspensionState) {
        ProcessDefinitionQuery query = repositoryService.createProcessDefinitionQuery();
        if (key != null && !key.isEmpty()) {
            query.processDefinitionKey(key);
        }
        if (name != null && !name.isEmpty()) {
            query.processDefinitionNameLike("%" + name + "%");
        }
        if (suspensionState != null && suspensionState == 1) {
            query.active();
        }
        else if (suspensionState != null && suspensionState == 2) {
            query.suspended();
        }
        query.orderByProcessDefinitionKey().asc().orderByProcessDefinitionVersion().desc();
        return success(buildList(query.list()));
    }

    @GetMapping("/simple-list")
    @Operation(summary = "获得流程定义精简列表（仅最新版本，下拉用）")
    public CommonResult<List<FlowDefinitionRespVO>> getSimpleProcessDefinitionList() {
        List<ProcessDefinition> definitions = repositoryService.createProcessDefinitionQuery()
                .latestVersion().active().orderByProcessDefinitionName().asc().list();
        return success(buildList(definitions));
    }

    @GetMapping("/get")
    @Operation(summary = "获得流程定义详情")
    public CommonResult<FlowDefinitionRespVO> getProcessDefinition(
            @RequestParam(value = "id", required = false) String id,
            @RequestParam(value = "key", required = false) String key) {
        ProcessDefinition definition;
        if (id != null && !id.isEmpty()) {
            definition = repositoryService.getProcessDefinition(id);
        }
        else if (key != null && !key.isEmpty()) {
            definition = repositoryService.createProcessDefinitionQuery()
                    .processDefinitionKey(key).latestVersion().singleResult();
        }
        else {
            return success(null);
        }
        return success(definition == null ? null : buildList(List.of(definition)).get(0));
    }

    private List<FlowDefinitionRespVO> buildList(List<ProcessDefinition> definitions) {
        // 部署时间批量补齐
        Map<String, Deployment> deploymentMap = new HashMap<>();
        for (ProcessDefinition definition : definitions) {
            if (!deploymentMap.containsKey(definition.getDeploymentId())) {
                Deployment deployment = repositoryService.createDeploymentQuery()
                        .deploymentId(definition.getDeploymentId()).singleResult();
                if (deployment != null) {
                    deploymentMap.put(deployment.getId(), deployment);
                }
            }
        }
        List<FlowDefinitionRespVO> result = new ArrayList<>();
        for (ProcessDefinition definition : definitions) {
            FlowDefinitionRespVO vo = new FlowDefinitionRespVO();
            vo.setId(definition.getId());
            vo.setKey(definition.getKey());
            vo.setName(definition.getName());
            vo.setVersion(definition.getVersion());
            vo.setCategory(definition.getCategory());
            vo.setDescription(definition.getDescription());
            vo.setSuspensionState(definition.isSuspended() ? 2 : 1);
            Deployment deployment = deploymentMap.get(definition.getDeploymentId());
            if (deployment != null) {
                vo.setDeploymentTime(deployment.getDeploymentTime());
            }
            result.add(vo);
        }
        return result;
    }

}
