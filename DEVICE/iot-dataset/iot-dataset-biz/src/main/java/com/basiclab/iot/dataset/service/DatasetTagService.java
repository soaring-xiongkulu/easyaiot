package com.basiclab.iot.dataset.service;

import javax.validation.*;
import com.basiclab.iot.common.domain.PageResult;
import com.basiclab.iot.dataset.dal.dataobject.DatasetTagDO;
import com.basiclab.iot.dataset.domain.dataset.vo.DatasetTagPageReqVO;
import com.basiclab.iot.dataset.domain.dataset.vo.DatasetTagSaveReqVO;

/**
 * 数据集标签 Service 接口
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
public interface DatasetTagService {

    /**
     * 创建数据集标签
     *
     * @param createReqVO 创建信息
     * @return 编号
     */
    Long createDatasetTag(@Valid DatasetTagSaveReqVO createReqVO);

    /**
     * 更新数据集标签
     *
     * @param updateReqVO 更新信息
     */
    void updateDatasetTag(@Valid DatasetTagSaveReqVO updateReqVO);

    /**
     * 删除数据集标签
     *
     * @param id 编号
     */
    void deleteDatasetTag(Long id);

    /**
     * 获得数据集标签
     *
     * @param id 编号
     * @return 数据集标签
     */
    DatasetTagDO getDatasetTag(Long id);

    /**
     * 获得数据集标签分页
     *
     * @param pageReqVO 分页查询
     * @return 数据集标签分页
     */
    PageResult<DatasetTagDO> getDatasetTagPage(DatasetTagPageReqVO pageReqVO);

}