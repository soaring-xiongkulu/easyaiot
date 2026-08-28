package com.basiclab.iot.flow.service.notify;

import java.util.List;

/**
 * FLOW 站内信通知 Service 接口
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
public interface FlowNotifyService {

    /**
     * 待办任务创建提醒：给责任人发站内信，内容含 deepLink（flow://instance/{id}?taskId={taskId}）
     *
     * 任何失败只记 warn，不影响引擎事务。
     *
     * @param processInstanceId 流程实例 ID
     * @param taskId            任务 ID
     * @param taskName          任务（节点）名
     * @param userIds           责任人集合
     */
    void notifyTaskTodo(String processInstanceId, String taskId, String taskName, List<Long> userIds);

}
