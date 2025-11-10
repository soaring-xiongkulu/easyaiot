package com.basiclab.iot.dataset.service;

import com.basiclab.iot.common.domain.PageResult;
import com.basiclab.iot.dataset.dal.dataobject.DatasetFrameTaskDO;
import com.basiclab.iot.dataset.domain.dataset.vo.DatasetFrameTaskPageReqVO;
import com.basiclab.iot.dataset.domain.dataset.vo.DatasetFrameTaskSaveReqVO;

import javax.validation.Valid;

/**
 * 视频流帧捕获任务 Service 接口
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
public interface DatasetFrameTaskService {

    /**
     * 创建视频流帧捕获任务
     *
     * @param createReqVO 创建信息
     * @return 编号
     */
    Long createDatasetFrameTask(@Valid DatasetFrameTaskSaveReqVO createReqVO);

    /**
     * 更新视频流帧捕获任务
     *
     * @param updateReqVO 更新信息
     */
    void updateDatasetFrameTask(@Valid DatasetFrameTaskSaveReqVO updateReqVO);

    /**
     * 删除视频流帧捕获任务
     *
     * @param id 编号
     */
    void deleteDatasetFrameTask(Long id);

    /**
     * 获得视频流帧捕获任务
     *
     * @param id 编号
     * @return 视频流帧捕获任务
     */
    DatasetFrameTaskDO getDatasetFrameTask(Long id);

    /**
     * 获得视频流帧捕获任务分页
     *
     * @param pageReqVO 分页查询
     * @return 视频流帧捕获任务分页
     */
    PageResult<DatasetFrameTaskDO> getDatasetFrameTaskPage(DatasetFrameTaskPageReqVO pageReqVO);

}