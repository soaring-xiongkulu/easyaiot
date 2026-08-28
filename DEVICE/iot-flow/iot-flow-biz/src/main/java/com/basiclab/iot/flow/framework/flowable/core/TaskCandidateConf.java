package com.basiclab.iot.flow.framework.flowable.core;

import lombok.Data;
import org.flowable.bpmn.model.ExtensionAttribute;
import org.flowable.bpmn.model.ExtensionElement;

import java.util.List;

/**
 * 审批节点候选人配置（从 BPMN 扩展元素 candidateConf 解析）
 */
@Data
public class TaskCandidateConf {

    private Integer candidateStrategy;
    private String candidateParam;
    private Integer approveMethod;
    private Integer approveRatio;
    private Boolean reasonRequire;
    private Integer assignEmptyHandlerType;
    private List<Long> assignEmptyUserIds;
    private Integer assignStartUserHandlerType;
    private Integer rejectHandlerType;
    private String rejectReturnNodeId;

    /** 解析扩展属性（可能为 null，如旧版模型） */
    public static TaskCandidateConf parse(ExtensionElement ext) {
        TaskCandidateConf conf = new TaskCandidateConf();
        if (ext == null) {
            return conf;
        }
        conf.setCandidateStrategy(intAttr(ext, EXT.STRATEGY));
        conf.setCandidateParam(strAttr(ext, EXT.PARAM));
        conf.setApproveMethod(intAttr(ext, EXT.METHOD));
        conf.setApproveRatio(intAttr(ext, EXT.RATIO));
        conf.setReasonRequire(boolAttr(ext, EXT.REASON_REQUIRE));
        conf.setAssignEmptyHandlerType(intAttr(ext, EXT.ASSIGN_EMPTY));
        conf.setAssignEmptyUserIds(longListAttr(ext, EXT.ASSIGN_EMPTY_USERS));
        conf.setAssignStartUserHandlerType(intAttr(ext, EXT.ASSIGN_START_USER));
        conf.setRejectHandlerType(intAttr(ext, EXT.REJECT_TYPE));
        conf.setRejectReturnNodeId(strAttr(ext, EXT.REJECT_RETURN));
        return conf;
    }

    private static int intAttr(ExtensionElement ext, String name) {
        String value = strAttr(ext, name);
        try {
            return value == null ? -1 : Integer.parseInt(value.trim());
        }
        catch (NumberFormatException e) {
            return -1;
        }
    }

    private static Boolean boolAttr(ExtensionElement ext, String name) {
        String value = strAttr(ext, name);
        return value == null ? null : Boolean.parseBoolean(value);
    }

    private static List<Long> longListAttr(ExtensionElement ext, String name) {
        String value = strAttr(ext, name);
        if (value == null || value.isEmpty()) {
            return null;
        }
        return java.util.Arrays.stream(value.split(","))
                .map(String::trim).filter(s -> s.matches("\\d+"))
                .map(Long::valueOf).toList();
    }

    private static String strAttr(ExtensionElement ext, String name) {
        List<ExtensionAttribute> attrs = ext.getAttributes().get(name);
        if (attrs == null || attrs.isEmpty()) {
            return null;
        }
        return attrs.get(0).getValue();
    }

    /** 属性名常量（与 SimpleModelConverter 一致） */
    public interface EXT {
        String STRATEGY = SimpleModelConverter.EXT_CONF_STRATEGY;
        String PARAM = SimpleModelConverter.EXT_CONF_PARAM;
        String METHOD = SimpleModelConverter.EXT_CONF_METHOD;
        String RATIO = SimpleModelConverter.EXT_CONF_RATIO;
        String REASON_REQUIRE = SimpleModelConverter.EXT_CONF_REASON_REQUIRE;
        String ASSIGN_EMPTY = SimpleModelConverter.EXT_CONF_ASSIGN_EMPTY;
        String ASSIGN_EMPTY_USERS = SimpleModelConverter.EXT_CONF_ASSIGN_EMPTY_USERS;
        String ASSIGN_START_USER = SimpleModelConverter.EXT_CONF_ASSIGN_START_USER;
        String REJECT_TYPE = SimpleModelConverter.EXT_CONF_REJECT_TYPE;
        String REJECT_RETURN = SimpleModelConverter.EXT_CONF_REJECT_RETURN;
    }
}
