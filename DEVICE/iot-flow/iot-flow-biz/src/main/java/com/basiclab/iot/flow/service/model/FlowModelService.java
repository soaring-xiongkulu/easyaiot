package com.basiclab.iot.flow.service.model;

import com.basiclab.iot.common.domain.PageParam;
import com.basiclab.iot.common.domain.PageResult;
import lombok.Data;

import java.io.Serializable;
import java.util.Date;

/**
 * 流程模型 Service 接口
 */
public interface FlowModelService {

    PageResult<FlowModelPageItem> getModelPage(PageParam pageParam, String key, String name, String category);

    FlowModelDetail getModel(String id);

    /** 读取 Simple 设计器 JSON（原始对象树） */
    Object getModelSimple(String id);

    String createModel(FlowModelSaveParams params);

    void updateModel(FlowModelSaveParams params);

    void updateModelSimple(String id, Object simpleModel);

    void deleteModel(String id);

    String copyModel(String id);

    /** 部署模型，返回流程定义 ID */
    String deployModel(String id);

    /** state：1 激活 / 2 挂起 */
    void updateModelState(String id, Integer state);

    /** 模型保存参数 */
    @Data
    class FlowModelSaveParams implements Serializable {

        private static final long serialVersionUID = 1L;

        private String id;
        private String name;
        private String key;
        private String category;
        private String icon;
        private String description;
        /** 模型类型：1 告警处理 / 2 通用审批等 */
        private Integer type;
        /** 表单类型：10 Simple 设计器表单（默认） */
        private Integer formType;

    }

    /** 模型分页条目（与前端 FlowModelVO 对齐） */
    @Data
    class FlowModelPageItem implements Serializable {

        private static final long serialVersionUID = 1L;

        private String id;
        private String key;
        private String name;
        private String category;
        private String icon;
        private String description;
        private Integer type;
        private Integer formType;
        private Date createTime;
        private Definition processDefinition;

        /** 最新流程定义（未部署为 null） */
        @Data
        public static class Definition implements Serializable {

            private static final long serialVersionUID = 1L;

            private String id;
            private String key;
            private String name;
            private Integer version;
            /** 1 激活 / 2 挂起 */
            private Integer suspensionState;
            private Date deploymentTime;

        }

    }

    /** 模型详情（含 Simple 设计器 JSON） */
    @Data
    class FlowModelDetail implements Serializable {

        private static final long serialVersionUID = 1L;

        private String id;
        private String key;
        private String name;
        private String category;
        private String icon;
        private String description;
        private Integer type;
        private Integer formType;
        /** Simple 设计器 JSON 树 */
        private Object simpleModel;

    }

}
