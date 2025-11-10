package com.basiclab.iot.dataset.service;

import javax.validation.*;
import com.basiclab.iot.common.domain.PageResult;
import com.basiclab.iot.dataset.dal.dataobject.DatasetTaskUserDO;
import com.basiclab.iot.dataset.domain.dataset.vo.DatasetTaskUserPageReqVO;
import com.basiclab.iot.dataset.domain.dataset.vo.DatasetTaskUserSaveReqVO;

/**
 * 标注任务用户 Service 接口
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
public interface DatasetTaskUserService {

    /**
     * 创建标注任务用户
     *
     * @param createReqVO 创建信息
     * @return 编号
     */
    Long createDatasetTaskUser(@Valid DatasetTaskUserSaveReqVO createReqVO);

    /**
     * 更新标注任务用户
     *
     * @param updateReqVO 更新信息
     */
    void updateDatasetTaskUser(@Valid DatasetTaskUserSaveReqVO updateReqVO);

    /**
     * 删除标注任务用户
     *
     * @param id 编号
     */
    void deleteDatasetTaskUser(Long id);

    /**
     * 获得标注任务用户
     *
     * @param id 编号
     * @return 标注任务用户
     */
    DatasetTaskUserDO getDatasetTaskUser(Long id);

    /**
     * 获得标注任务用户分页
     *
     * @param pageReqVO 分页查询
     * @return 标注任务用户分页
     */
    PageResult<DatasetTaskUserDO> getDatasetTaskUserPage(DatasetTaskUserPageReqVO pageReqVO);

}