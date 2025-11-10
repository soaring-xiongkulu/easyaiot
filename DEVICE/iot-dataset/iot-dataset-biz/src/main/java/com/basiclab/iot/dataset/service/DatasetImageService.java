package com.basiclab.iot.dataset.service;

import com.basiclab.iot.common.domain.PageResult;
import com.basiclab.iot.dataset.dal.dataobject.DatasetImageDO;
import com.basiclab.iot.dataset.domain.dataset.vo.DatasetImagePageReqVO;
import com.basiclab.iot.dataset.domain.dataset.vo.DatasetImageSaveReqVO;
import org.springframework.web.multipart.MultipartFile;

import javax.validation.Valid;
import java.math.BigDecimal;
import java.util.List;

/**
 * 图片数据集 Service 接口
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
public interface DatasetImageService {

    /**
     * 创建图片数据集
     *
     * @param createReqVO 创建信息
     * @return 编号
     */
    Long createDatasetImage(@Valid DatasetImageSaveReqVO createReqVO);

    /**
     * 更新图片数据集
     *
     * @param updateReqVO 更新信息
     */
    void updateDatasetImage(@Valid DatasetImageSaveReqVO updateReqVO);

    /**
     * 删除图片数据集
     *
     * @param id 编号
     */
    void deleteDatasetImage(Long id);

    /**
     * 批量删除图片数据集
     *
     * @param ids 编号列表
     */
    void deleteDatasetImages(List<Long> ids);

    /**
     * 获得图片数据集
     *
     * @param id 编号
     * @return 图片数据集
     */
    DatasetImageDO getDatasetImage(Long id);

    /**
     * 获得图片数据集分页
     *
     * @param pageReqVO 分页查询
     * @return 图片数据集分页
     */
    PageResult<DatasetImageDO> getDatasetImagePage(DatasetImagePageReqVO pageReqVO);

    /**
     * 分割数据集
     *
     * @param datasetId
     * @param trainRatio
     * @param valRatio
     * @param testRatio
     */
    void splitDataset(Long datasetId, BigDecimal trainRatio, BigDecimal valRatio, BigDecimal testRatio);

    /**
     * 重置数据集使用状态
     *
     * @param datasetId
     */
    void resetUsageByDatasetId(Long datasetId);

    /**
     * 上传图片数据集
     *
     * @param file
     * @param datasetId
     * @param isZip
     */
    void processUpload(MultipartFile file, Long datasetId, Boolean isZip);


    /**
     * 上传文件
     *
     * @param file
     * @return
     * @throws Exception
     */
    String uploadFile(MultipartFile file) throws Exception;


    /**
     * 检查数据集同步条件
     *
     * @param datasetId 数据集ID
     * @return 是否满足同步条件
     */
    boolean checkSyncCondition(Long datasetId);

    /**
     * 同步数据集到Minio
     *
     * @param datasetId 数据集ID
     */
    String syncToMinio(Long datasetId);
}