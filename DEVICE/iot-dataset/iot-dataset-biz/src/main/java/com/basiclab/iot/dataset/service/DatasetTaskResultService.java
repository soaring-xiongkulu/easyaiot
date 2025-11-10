package com.basiclab.iot.dataset.service;

import javax.validation.*;
import com.basiclab.iot.common.domain.PageResult;
import com.basiclab.iot.dataset.dal.dataobject.DatasetTaskResultDO;
import com.basiclab.iot.dataset.domain.dataset.vo.DatasetTaskResultPageReqVO;
import com.basiclab.iot.dataset.domain.dataset.vo.DatasetTaskResultSaveReqVO;

/**
 * 标注任务结果 Service 接口
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
public interface DatasetTaskResultService {

    /**
     * 创建标注任务结果
     *
     * @param createReqVO 创建信息
     * @return 编号
     */
    Long createDatasetTaskResult(@Valid DatasetTaskResultSaveReqVO createReqVO);

    /**
     * 更新标注任务结果
     *
     * @param updateReqVO 更新信息
     */
    void updateDatasetTaskResult(@Valid DatasetTaskResultSaveReqVO updateReqVO);

    /**
     * 删除标注任务结果
     *
     * @param id 编号
     */
    void deleteDatasetTaskResult(Long id);

    /**
     * 获得标注任务结果
     *
     * @param id 编号
     * @return 标注任务结果
     */
    DatasetTaskResultDO getDatasetTaskResult(Long id);

    /**
     * 获得标注任务结果分页
     *
     * @param pageReqVO 分页查询
     * @return 标注任务结果分页
     */
    PageResult<DatasetTaskResultDO> getDatasetTaskResultPage(DatasetTaskResultPageReqVO pageReqVO);

}