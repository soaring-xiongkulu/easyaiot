package com.basiclab.iot.dataset.service;

import javax.validation.*;
import com.basiclab.iot.common.domain.PageResult;
import com.basiclab.iot.dataset.dal.dataobject.DatasetTaskDO;
import com.basiclab.iot.dataset.domain.dataset.vo.DatasetTaskPageReqVO;
import com.basiclab.iot.dataset.domain.dataset.vo.DatasetTaskSaveReqVO;

/**
 * 标注任务 Service 接口
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
public interface DatasetTaskService {

    /**
     * 创建标注任务
     *
     * @param createReqVO 创建信息
     * @return 编号
     */
    Long createDatasetTask(@Valid DatasetTaskSaveReqVO createReqVO);

    /**
     * 更新标注任务
     *
     * @param updateReqVO 更新信息
     */
    void updateDatasetTask(@Valid DatasetTaskSaveReqVO updateReqVO);

    /**
     * 删除标注任务
     *
     * @param id 编号
     */
    void deleteDatasetTask(Long id);

    /**
     * 获得标注任务
     *
     * @param id 编号
     * @return 标注任务
     */
    DatasetTaskDO getDatasetTask(Long id);

    /**
     * 获得标注任务分页
     *
     * @param pageReqVO 分页查询
     * @return 标注任务分页
     */
    PageResult<DatasetTaskDO> getDatasetTaskPage(DatasetTaskPageReqVO pageReqVO);

}