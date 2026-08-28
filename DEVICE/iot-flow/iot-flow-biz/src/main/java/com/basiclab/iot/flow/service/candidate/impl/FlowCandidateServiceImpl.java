package com.basiclab.iot.flow.service.candidate.impl;

import com.basiclab.iot.flow.dal.dataobject.FlowUserGroupDO;
import com.basiclab.iot.flow.dal.pgsql.FlowUserGroupMapper;
import com.basiclab.iot.flow.dal.pgsql.SystemUserRoleMapper;
import com.basiclab.iot.flow.framework.flowable.core.TaskCandidateConf;
import com.basiclab.iot.flow.service.candidate.FlowCandidateService;
import com.basiclab.iot.system.api.dept.DeptApi;
import com.basiclab.iot.system.api.user.AdminUserApi;
import com.basiclab.iot.system.api.user.dto.AdminUserRespDTO;
import lombok.extern.slf4j.Slf4j;
import org.flowable.bpmn.model.ExtensionElement;
import org.springframework.stereotype.Service;

import javax.annotation.Resource;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collection;
import java.util.Collections;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.stream.Collectors;

/**
 * 候选人解析实现：策略 10 种，详见 {@link com.basiclab.iot.flow.enums.CandidateStrategy}
 */
@Slf4j
@Service
public class FlowCandidateServiceImpl implements FlowCandidateService {

    /** 发起人自选变量（Map<nodeId, List<userId>>） */
    public static final String START_USER_SELECT_VAR = "startUserSelectAssignees";

    @Resource
    private AdminUserApi adminUserApi;
    @Resource
    private DeptApi deptApi;
    @Resource
    private SystemUserRoleMapper systemUserRoleMapper;
    @Resource
    private FlowUserGroupMapper userGroupMapper;

    @Override
    public List<Long> resolve(TaskCandidateConf conf, Long startUserId, Map<String, Object> variables, String nodeId) {
        if (conf == null || conf.getCandidateStrategy() == null) {
            return Collections.emptyList();
        }
        Set<Long> userIds = new LinkedHashSet<>();
        int strategy = conf.getCandidateStrategy();
        List<Long> paramIds = parseIds(conf.getCandidateParam());
        switch (strategy) {
            case 10 -> userIds.addAll(systemUserRoleMapper.selectUserIdsByRoleIds(paramIds));
            case 20 -> userIds.addAll(rpcUserIdsByDepts(paramIds));
            case 21 -> userIds.addAll(deptLeaders(paramIds));
            case 22 -> {
                List<AdminUserRespDTO> postUsers = adminUserApi.getUserListByPostIds(paramIds).getCheckedData();
                userIds.addAll(postUsers.stream().map(AdminUserRespDTO::getId).toList());
            }
            case 30 -> userIds.addAll(paramIds);
            case 34 -> {
                // 审批人自选：运行期由上一节点通过变量注入，启动期解析不到则走审批人为空逻辑
                userIds.addAll(variableSelected(variables, nodeId));
            }
            case 35 -> userIds.addAll(variableSelected(variables, nodeId));
            case 36 -> {
                if (startUserId != null) {
                    userIds.add(startUserId);
                }
            }
            case 37 -> {
                Long deptId = getUserDeptId(startUserId);
                if (deptId != null) {
                    userIds.addAll(deptLeaders(List.of(deptId)));
                }
            }
            case 40 -> userIds.addAll(userGroupMembers(paramIds));
            default -> log.warn("[resolve] 未支持的候选人策略: {}", strategy);
        }
        return normalize(userIds);
    }

    @Override
    public List<Long> resolveAssignEmpty(TaskCandidateConf conf, Long startUserId) {
        if (conf == null || conf.getAssignEmptyHandlerType() == null) {
            return Collections.emptyList();
        }
        return switch (conf.getAssignEmptyHandlerType()) {
            case 3 -> normalize(new LinkedHashSet<>(conf.getAssignEmptyUserIds() == null
                    ? Collections.<Long>emptyList() : conf.getAssignEmptyUserIds()));
            case 4 -> startUserId == null ? Collections.emptyList() : List.of(startUserId);
            default -> Collections.emptyList();
        };
    }

    @Override
    public Map<Long, String> getUserNicknameMap(Collection<Long> userIds) {
        if (userIds == null || userIds.isEmpty()) {
            return Collections.emptyMap();
        }
        List<AdminUserRespDTO> users = adminUserApi.getUserList(userIds).getCheckedData();
        return users.stream().collect(Collectors.toMap(AdminUserRespDTO::getId, AdminUserRespDTO::getNickname, (a, b) -> a));
    }

    // ---------- 策略内部 ----------

    private List<Long> variableSelected(Map<String, Object> variables, String nodeId) {
        if (variables == null || nodeId == null) {
            return Collections.emptyList();
        }
        Object selectVar = variables.get(START_USER_SELECT_VAR);
        if (!(selectVar instanceof Map<?, ?> selectMap)) {
            return Collections.emptyList();
        }
        Object value = selectMap.get(nodeId);
        if (value instanceof Collection<?> list) {
            return list.stream().map(v -> Long.valueOf(String.valueOf(v))).toList();
        }
        return Collections.emptyList();
    }

    private List<Long> rpcUserIdsByDepts(Collection<Long> deptIds) {
        List<AdminUserRespDTO> users = adminUserApi.getUserListByDeptIds(deptIds).getCheckedData();
        return users.stream().map(AdminUserRespDTO::getId).toList();
    }

    private List<Long> deptLeaders(Collection<Long> deptIds) {
        Set<Long> leaders = new LinkedHashSet<>();
        for (com.basiclab.iot.system.api.dept.dto.DeptRespDTO dept : deptApi.getDeptList(deptIds).getCheckedData()) {
            if (dept.getLeaderUserId() != null) {
                leaders.add(dept.getLeaderUserId());
            }
        }
        return new ArrayList<>(leaders);
    }

    private List<Long> userGroupMembers(Collection<Long> groupIds) {
        Set<Long> members = new LinkedHashSet<>();
        for (Long groupId : groupIds) {
            FlowUserGroupDO group = userGroupMapper.selectById(groupId);
            if (group != null && group.getMemberUserIds() != null) {
                members.addAll(group.getMemberUserIds());
            }
        }
        return new ArrayList<>(members);
    }

    private Long getUserDeptId(Long userId) {
        if (userId == null) {
            return null;
        }
        AdminUserRespDTO user = adminUserApi.getUser(userId).getCheckedData();
        return user == null ? null : user.getDeptId();
    }

    /** 审批人与发起人相同的处理（在指派前调用，返回调整后的候选人） */
    public List<Long> applyAssignStartUserHandler(TaskCandidateConf conf, List<Long> candidateIds, Long startUserId) {
        if (candidateIds.size() != 1 || startUserId == null || !candidateIds.contains(startUserId)) {
            return candidateIds;
        }
        int handler = conf == null || conf.getAssignStartUserHandlerType() == null ? 1 : conf.getAssignStartUserHandlerType();
        return switch (handler) {
            case 2 -> Collections.emptyList(); // 自动跳过
            case 3 -> { // 转交部门负责人
                Long deptId = getUserDeptId(startUserId);
                yield deptId == null ? candidateIds : deptLeaders(List.of(deptId));
            }
            default -> candidateIds;
        };
    }

    private List<Long> parseIds(String param) {
        if (param == null || param.isEmpty()) {
            return Collections.emptyList();
        }
        return Arrays.stream(param.split(","))
                .map(String::trim).filter(s -> s.matches("\\d+"))
                .map(Long::valueOf).distinct().collect(Collectors.toList());
    }

    /** 去重 + 过滤停用用户 + 排序 */
    private List<Long> normalize(Set<Long> userIds) {
        if (userIds.isEmpty()) {
            return Collections.emptyList();
        }
        Map<Long, AdminUserRespDTO> userMap = adminUserApi.getUserMap(userIds);
        return userIds.stream()
                .filter(userMap::containsKey)
                .filter(id -> userMap.get(id).getStatus() == null || userMap.get(id).getStatus() == 0)
                .sorted()
                .collect(Collectors.toList());
    }

    /** 扩展元素解析入口（供 listener 使用） */
    public TaskCandidateConf parseConf(ExtensionElement ext) {
        return TaskCandidateConf.parse(ext);
    }

}
