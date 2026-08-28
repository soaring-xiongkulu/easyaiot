package com.basiclab.iot.flow.service.model;

import com.basiclab.iot.common.domain.PageParam;
import com.basiclab.iot.common.domain.PageResult;
import com.basiclab.iot.common.utils.json.JsonUtils;
import com.basiclab.iot.flow.framework.flowable.core.SimpleFlowNodeVO;
import com.basiclab.iot.flow.framework.flowable.core.SimpleModelConverter;
import com.basiclab.iot.flow.service.model.FlowModelService.FlowModelDetail;
import com.basiclab.iot.flow.service.model.FlowModelService.FlowModelPageItem;
import com.basiclab.iot.flow.service.model.FlowModelService.FlowModelSaveParams;
import com.fasterxml.jackson.databind.JsonNode;
import lombok.extern.slf4j.Slf4j;
import org.flowable.bpmn.converter.BpmnXMLConverter;
import org.flowable.bpmn.model.BpmnModel;
import org.flowable.engine.RepositoryService;
import org.flowable.engine.repository.Deployment;
import org.flowable.engine.repository.Model;
import org.flowable.engine.repository.ModelQuery;
import org.flowable.engine.repository.ProcessDefinition;
import org.springframework.stereotype.Service;

import javax.annotation.Resource;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

import static com.basiclab.iot.common.exception.util.ServiceExceptionUtil.exception;
import static com.basiclab.iot.flow.enums.FlowErrorCodeConstants.MODEL_KEY_EXISTS;
import static com.basiclab.iot.flow.enums.FlowErrorCodeConstants.MODEL_NOT_EXISTS;
import static com.basiclab.iot.flow.enums.FlowErrorCodeConstants.MODEL_SIMPLE_MODEL_INVALID;

/**
 * 流程模型 Service：ACT_RE_MODEL 承载 Simple 设计器 JSON（模型源）+ 元信息（metaInfo）
 */
@Slf4j
@Service
public class FlowModelServiceImpl implements FlowModelService {

    @Resource
    private RepositoryService repositoryService;

    // ==================== 查询 ====================

    @Override
    public PageResult<FlowModelPageItem> getModelPage(PageParam pageParam, String key, String name, String category) {
        ModelQuery query = repositoryService.createModelQuery();
        if (key != null && !key.isEmpty()) {
            query.modelKey(key);
        }
        if (name != null && !name.isEmpty()) {
            query.modelNameLike("%" + name + "%");
        }
        if (category != null && !category.isEmpty()) {
            query.modelCategory(category);
        }
        query.orderByCreateTime().desc();
        long total = query.count();
        List<Model> models = query.listPage((pageParam.getPageNo() - 1) * pageParam.getPageSize(), pageParam.getPageSize());
        List<FlowModelPageItem> items = new ArrayList<>();
        for (Model model : models) {
            items.add(buildPageItem(model));
        }
        return new PageResult<>(items, total);
    }

    private FlowModelPageItem buildPageItem(Model model) {
        FlowModelPageItem item = new FlowModelPageItem();
        item.setId(model.getId());
        item.setKey(model.getKey());
        item.setName(model.getName());
        item.setCategory(model.getCategory());
        item.setCreateTime(model.getCreateTime());
        JsonNode meta = metaInfo(model);
        if (meta != null) {
            if (meta.hasNonNull("icon")) {
                item.setIcon(meta.get("icon").asText());
            }
            if (meta.hasNonNull("description")) {
                item.setDescription(meta.get("description").asText());
            }
            if (meta.hasNonNull("type")) {
                item.setType(meta.get("type").asInt());
            }
            if (meta.hasNonNull("formType")) {
                item.setFormType(meta.get("formType").asInt());
            }
        }
        // 最新已部署定义
        ProcessDefinition definition = repositoryService.createProcessDefinitionQuery()
                .processDefinitionKey(model.getKey()).latestVersion().singleResult();
        if (definition != null) {
            FlowModelPageItem.Definition defVO = new FlowModelPageItem.Definition();
            defVO.setId(definition.getId());
            defVO.setKey(definition.getKey());
            defVO.setName(definition.getName());
            defVO.setVersion(definition.getVersion());
            defVO.setSuspensionState(definition.isSuspended() ? 2 : 1);
            Deployment deployment = repositoryService.createDeploymentQuery()
                    .deploymentId(definition.getDeploymentId()).singleResult();
            if (deployment != null) {
                defVO.setDeploymentTime(deployment.getDeploymentTime());
            }
            item.setProcessDefinition(defVO);
        }
        return item;
    }

    @Override
    public FlowModelDetail getModel(String id) {
        Model model = repositoryService.getModel(id);
        if (model == null) {
            throw exception(MODEL_NOT_EXISTS);
        }
        FlowModelDetail detail = new FlowModelDetail();
        detail.setId(model.getId());
        detail.setKey(model.getKey());
        detail.setName(model.getName());
        detail.setCategory(model.getCategory());
        JsonNode meta = metaInfo(model);
        if (meta != null) {
            if (meta.hasNonNull("icon")) {
                detail.setIcon(meta.get("icon").asText());
            }
            if (meta.hasNonNull("description")) {
                detail.setDescription(meta.get("description").asText());
            }
            if (meta.hasNonNull("type")) {
                detail.setType(meta.get("type").asInt());
            }
            if (meta.hasNonNull("formType")) {
                detail.setFormType(meta.get("formType").asInt());
            }
        }
        detail.setSimpleModel(readSimpleModel(model));
        return detail;
    }

    @Override
    public Object getModelSimple(String id) {
        return readSimpleModel(repositoryService.getModel(id));
    }

    // ==================== 增删改 ====================

    @Override
    public String createModel(FlowModelSaveParams params) {
        if (repositoryService.createModelQuery().modelKey(params.getKey()).count() > 0) {
            throw exception(MODEL_KEY_EXISTS);
        }
        Model model = repositoryService.newModel();
        model.setKey(params.getKey());
        model.setName(params.getName());
        model.setCategory(params.getCategory());
        model.setMetaInfo(buildMetaInfo(params));
        repositoryService.saveModel(model);
        // 默认 Simple 模型：发起人 -> 审批 -> 结束
        repositoryService.addModelEditorSource(model.getId(), defaultSimpleModel(params.getName()));
        return model.getId();
    }

    @Override
    public void updateModel(FlowModelSaveParams params) {
        Model model = repositoryService.getModel(params.getId());
        if (model == null) {
            throw exception(MODEL_NOT_EXISTS);
        }
        if (params.getKey() != null && !params.getKey().equals(model.getKey())
                && repositoryService.createModelQuery().modelKey(params.getKey()).count() > 0) {
            throw exception(MODEL_KEY_EXISTS);
        }
        if (params.getName() != null) {
            model.setName(params.getName());
        }
        if (params.getKey() != null) {
            model.setKey(params.getKey());
        }
        if (params.getCategory() != null) {
            model.setCategory(params.getCategory());
        }
        model.setMetaInfo(buildMetaInfo(params));
        repositoryService.saveModel(model);
    }

    @Override
    public void updateModelSimple(String id, Object simpleModel) {
        Model model = repositoryService.getModel(id);
        if (model == null) {
            throw exception(MODEL_NOT_EXISTS);
        }
        repositoryService.addModelEditorSource(id,
                JsonUtils.toJsonString(simpleModel).getBytes(StandardCharsets.UTF_8));
    }

    @Override
    public void deleteModel(String id) {
        Model model = repositoryService.getModel(id);
        if (model == null) {
            throw exception(MODEL_NOT_EXISTS);
        }
        // 删除该 key 全部版本的部署（有运行实例时 Flowable 抛错，不级联）
        List<ProcessDefinition> definitions = repositoryService.createProcessDefinitionQuery()
                .processDefinitionKey(model.getKey()).list();
        for (ProcessDefinition definition : definitions) {
            repositoryService.deleteDeployment(definition.getDeploymentId(), false);
        }
        repositoryService.deleteModel(id);
    }

    @Override
    public String copyModel(String id) {
        Model model = repositoryService.getModel(id);
        if (model == null) {
            throw exception(MODEL_NOT_EXISTS);
        }
        Object simpleModel = readSimpleModel(model);
        FlowModelSaveParams params = new FlowModelSaveParams();
        params.setName(model.getName() + "_copy");
        params.setKey(model.getKey() + "_copy_" + System.currentTimeMillis() % 100000);
        params.setCategory(model.getCategory());
        JsonNode meta = metaInfo(model);
        if (meta != null) {
            if (meta.hasNonNull("icon")) {
                params.setIcon(meta.get("icon").asText());
            }
            if (meta.hasNonNull("description")) {
                params.setDescription(meta.get("description").asText());
            }
            if (meta.hasNonNull("type")) {
                params.setType(meta.get("type").asInt());
            }
        }
        String newId = createModel(params);
        if (simpleModel != null) {
            repositoryService.addModelEditorSource(newId,
                    JsonUtils.toJsonString(simpleModel).getBytes(StandardCharsets.UTF_8));
        }
        return newId;
    }

    // ==================== 部署 / 状态 ====================

    @Override
    public String deployModel(String id) {
        Model model = repositoryService.getModel(id);
        if (model == null) {
            throw exception(MODEL_NOT_EXISTS);
        }
        Object simpleModel = readSimpleModel(model);
        if (simpleModel == null) {
            throw exception(MODEL_SIMPLE_MODEL_INVALID);
        }
        SimpleFlowNodeVO root = JsonUtils.parseObject2(JsonUtils.toJsonString(simpleModel), SimpleFlowNodeVO.class);
        if (root == null || root.getChildNode() == null) {
            throw exception(MODEL_SIMPLE_MODEL_INVALID);
        }
        BpmnModel bpmnModel = new SimpleModelConverter(model.getKey(), model.getName()).convert(root);
        // 流程定义的 category 取自 <definitions> 的 targetNamespace（部署 category 不会覆盖它），这里显式写入
        if (model.getCategory() != null && !model.getCategory().isEmpty()) {
            bpmnModel.setTargetNamespace(model.getCategory());
        }
        byte[] xmlBytes = new BpmnXMLConverter().convertToXML(bpmnModel);
        Deployment deployment = repositoryService.createDeployment()
                .key(model.getKey())
                .name(model.getName())
                .category(model.getCategory())
                .addBytes(model.getKey() + ".bpmn", xmlBytes)
                .deploy();
        // metaInfo 记录最新部署 ID（模型页直接展示最新定义）
        JsonNode meta = metaInfo(model);
        Map<String, Object> metaMap = new HashMap<>();
        if (meta != null) {
            meta.fields().forEachRemaining(entry -> metaMap.put(entry.getKey(), entry.getValue()));
        }
        metaMap.put("deploymentId", deployment.getId());
        model.setMetaInfo(JsonUtils.toJsonString(metaMap));
        repositoryService.saveModel(model);
        log.info("[deployModel] 模型部署成功, modelId={}, key={}, deploymentId={}", id, model.getKey(), deployment.getId());
        ProcessDefinition definition = repositoryService.createProcessDefinitionQuery()
                .deploymentId(deployment.getId()).singleResult();
        return definition == null ? deployment.getId() : definition.getId();
    }

    @Override
    public void updateModelState(String id, Integer state) {
        Model model = repositoryService.getModel(id);
        if (model == null) {
            throw exception(MODEL_NOT_EXISTS);
        }
        ProcessDefinition definition = repositoryService.createProcessDefinitionQuery()
                .processDefinitionKey(model.getKey()).latestVersion().singleResult();
        if (definition == null) {
            throw exception(MODEL_NOT_EXISTS);
        }
        if (state != null && state == 1) {
            repositoryService.activateProcessDefinitionById(definition.getId());
        }
        else {
            repositoryService.suspendProcessDefinitionById(definition.getId());
        }
    }

    // ==================== 内部 ====================

    private JsonNode metaInfo(Model model) {
        String meta = model.getMetaInfo();
        return meta == null || meta.isEmpty() ? null : JsonUtils.parseTree(meta);
    }

    private Object readSimpleModel(Model model) {
        if (model == null) {
            return null;
        }
        byte[] source = repositoryService.getModelEditorSource(model.getId());
        if (source == null || source.length == 0) {
            return null;
        }
        return JsonUtils.parseObject(new String(source, StandardCharsets.UTF_8), Object.class);
    }

    private String buildMetaInfo(FlowModelSaveParams params) {
        Map<String, Object> meta = new HashMap<>();
        meta.put("name", params.getName());
        if (params.getDescription() != null) {
            meta.put("description", params.getDescription());
        }
        if (params.getCategory() != null) {
            meta.put("category", params.getCategory());
        }
        if (params.getIcon() != null) {
            meta.put("icon", params.getIcon());
        }
        meta.put("type", params.getType() == null ? 1 : params.getType());
        meta.put("formType", params.getFormType() == null ? 10 : params.getFormType());
        return JsonUtils.toJsonString(meta);
    }

    /** 默认流程：发起人 -> 一个审批节点 -> 结束 */
    private byte[] defaultSimpleModel(String name) {
        SimpleFlowNodeVO start = new SimpleFlowNodeVO();
        start.setId("start_user_1");
        start.setType(10);
        start.setName("发起人");

        SimpleFlowNodeVO task = new SimpleFlowNodeVO();
        task.setId("task_1");
        task.setType(11);
        task.setName("审批人");
        task.setApproveMethod(3);
        task.setCandidateStrategy(30);
        task.setCandidateParam("1");
        start.setChildNode(task);

        SimpleFlowNodeVO end = new SimpleFlowNodeVO();
        end.setId("end_1");
        end.setType(1);
        end.setName("结束");
        task.setChildNode(end);

        Map<String, Object> root = new HashMap<>();
        root.put("id", "root");
        root.put("type", 0);
        root.put("name", name == null ? "未命名流程" : name);
        root.put("childNode", start);
        return JsonUtils.toJsonString(root).getBytes(StandardCharsets.UTF_8);
    }

}
