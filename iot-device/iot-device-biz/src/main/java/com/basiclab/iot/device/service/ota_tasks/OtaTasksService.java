package com.basiclab.iot.device.service.ota_tasks;

import javax.validation.*;
import com.basiclab.iot.device.controller.admin.ota_tasks.vo.*;
import com.basiclab.iot.device.dal.dataobject.ota_tasks.OtaTasksDO;
import com.basiclab.iot.common.domain.PageResult;

/**
 * OTA升级任务 Service 接口
 *
 * @author BasicLab
 */
public interface OtaTasksService {

    /**
     * 创建OTA升级任务
     *
     * @param createReqVO 创建信息
     * @return 编号
     */
    Long createTasks(@Valid OtaTasksSaveReqVO createReqVO);

    /**
     * 更新OTA升级任务
     *
     * @param updateReqVO 更新信息
     */
    void updateTasks(@Valid OtaTasksSaveReqVO updateReqVO);

    /**
     * 删除OTA升级任务
     *
     * @param id 编号
     */
    void deleteTasks(Long id);

    /**
     * 获得OTA升级任务
     *
     * @param id 编号
     * @return OTA升级任务
     */
    OtaTasksDO getTasks(Long id);

    /**
     * 获得OTA升级任务分页
     *
     * @param pageReqVO 分页查询
     * @return OTA升级任务分页
     */
    PageResult<OtaTasksDO> getTasksPage(OtaTasksPageReqVO pageReqVO);

}