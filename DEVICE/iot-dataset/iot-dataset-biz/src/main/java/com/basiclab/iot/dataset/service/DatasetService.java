package com.basiclab.iot.dataset.service;

import com.basiclab.iot.common.domain.PageResult;
import com.basiclab.iot.dataset.dal.dataobject.DatasetDO;
import com.basiclab.iot.dataset.domain.dataset.vo.AutoLabelModelReqVO;
import com.basiclab.iot.dataset.domain.dataset.vo.DatasetPageReqVO;
import com.basiclab.iot.dataset.domain.dataset.vo.DatasetSaveReqVO;
import com.basiclab.iot.dataset.domain.dataset.vo.DatasetSplitReqVO;
import com.github.pagehelper.PageInfo;
import org.springframework.web.multipart.MultipartFile;

import javax.validation.Valid;
import java.util.List;

/**
 * 数据集 Service 接口
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
public interface DatasetService {

    /**
     * 创建数据集
     *
     * @param createReqVO 创建信息
     * @return 编号
     */
    Long createDataset(@Valid DatasetSaveReqVO createReqVO);

    /**
     * 更新数据集
     *
     * @param updateReqVO 更新信息
     */
    void updateDataset(@Valid DatasetSaveReqVO updateReqVO);

    /**
     * 删除数据集
     *
     * @param id 编号
     */
    void deleteDataset(Long id);

    /**
     * 获得数据集
     *
     * @param id 编号
     * @return 数据集
     */
    DatasetDO getDataset(Long id);

    /**
     * 获得数据集分页
     *
     * @param pageReqVO 分页查询
     * @return 数据集分页
     */
    PageInfo<DatasetDO> getDatasetPage(DatasetPageReqVO pageReqVO);

    /**
     * 上传数据集封面
     *
     * @param file
     * @return
     * @throws Exception
     */
    String uploadCover(MultipartFile file) throws Exception;

    /**
     * 设置自动标注模型
     *
     * @param datasetId
     * @param reqVO
     */
    void setAutoLabelModel(Long datasetId, AutoLabelModelReqVO reqVO);

    /**
     * 自动标注数据集
     *
     * @param datasetId
     */
    void autoLabelDataset(Long datasetId);

    /**
     * 分割数据集
     *
     * @param datasetId
     * @param reqVO
     */
    void splitDataset(Long datasetId, DatasetSplitReqVO reqVO);

    /**
     * 重置数据集
     *
     * @param datasetId
     */
    void resetDataset(Long datasetId);

}