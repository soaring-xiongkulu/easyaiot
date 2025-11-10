package com.basiclab.iot.dataset.service;

import com.basiclab.iot.common.domain.PageResult;
import com.basiclab.iot.dataset.dal.dataobject.DatasetVideoDO;
import com.basiclab.iot.dataset.domain.dataset.vo.DatasetVideoPageReqVO;
import com.basiclab.iot.dataset.domain.dataset.vo.DatasetVideoSaveReqVO;

import javax.validation.Valid;

/**
 * 视频数据集 Service 接口
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
public interface DatasetVideoService {

    /**
     * 创建视频数据集
     *
     * @param createReqVO 创建信息
     * @return 编号
     */
    Long createDatasetVideo(@Valid DatasetVideoSaveReqVO createReqVO);

    /**
     * 更新视频数据集
     *
     * @param updateReqVO 更新信息
     */
    void updateDatasetVideo(@Valid DatasetVideoSaveReqVO updateReqVO);

    /**
     * 删除视频数据集
     *
     * @param id 编号
     */
    void deleteDatasetVideo(Long id);

    /**
     * 获得视频数据集
     *
     * @param id 编号
     * @return 视频数据集
     */
    DatasetVideoDO getDatasetVideo(Long id);

    /**
     * 获得视频数据集分页
     *
     * @param pageReqVO 分页查询
     * @return 视频数据集分页
     */
    PageResult<DatasetVideoDO> getDatasetVideoPage(DatasetVideoPageReqVO pageReqVO);

}