package com.basiclab.iot.dataset.service;

import com.basiclab.iot.common.domain.PageResult;
import com.basiclab.iot.dataset.dal.dataobject.DatasetImageDO;
import com.basiclab.iot.dataset.domain.dataset.vo.DatasetImageImportItem;
import com.basiclab.iot.dataset.domain.dataset.vo.DatasetImagePageReqVO;
import com.basiclab.iot.dataset.domain.dataset.vo.DatasetImageSaveReqVO;
import com.basiclab.iot.dataset.domain.dataset.vo.DatasetImageUploadRespVO;
import com.basiclab.iot.dataset.domain.dataset.vo.DatasetSyncCheckRespVO;
import org.springframework.web.multipart.MultipartFile;

import javax.validation.Valid;
import java.math.BigDecimal;
import java.nio.file.Path;
import java.util.List;
import java.util.Map;

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

    /** 批量清除图片标注，并恢复为待标注状态。 */
    void clearDatasetImageAnnotations(List<Long> ids);

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
    DatasetImageUploadRespVO processUpload(MultipartFile file, Long datasetId, Boolean isZip);

    /**
     * 从本地合并后的文件处理上传（分片上传完成后调用）
     */
    DatasetImageUploadRespVO processUploadFromPath(Path filePath, String originalFilename,
                                                   Long datasetId, Boolean isZip);


    /**
     * 上传文件
     *
     * @param file
     * @return
     * @throws Exception
     */
    String uploadFile(MultipartFile file) throws Exception;


    /**
     * 检查数据集同步条件（用途划分、标注完成等）
     *
     * @param datasetId 数据集ID
     * @return 同步前置条件详情
     */
    DatasetSyncCheckRespVO checkSyncCondition(Long datasetId);

    /**
     * 同步数据集到Minio
     *
     * @param datasetId 数据集ID
     */
    String syncToMinio(Long datasetId);

    /**
     * 导入单张图片（可带标注 JSON，坐标为相对图片宽高的 0~1 归一化值）
     */
    Long saveImportedImage(Long datasetId, String filename, byte[] fileData,
                           String annotationsJson, Integer width, Integer height, Integer completed);

    /**
     * 批量导入图片（同名覆盖，批量入库）
     */
    DatasetImageUploadRespVO batchImportImages(Long datasetId, List<DatasetImageImportItem> items);

    /**
     * 批量导入图片，复用调用方维护的同名图片索引，避免每批重新全表查询。
     */
    DatasetImageUploadRespVO batchImportImages(Long datasetId, List<DatasetImageImportItem> items,
                                               Map<String, DatasetImageDO> existingByName);

    /**
     * 从 ZIP 文件流式分批导入（避免一次性加载全部图片到内存）
     *
     * @param progressCallback 已处理图片数量回调，可为 null
     */
    DatasetImageUploadRespVO importZipFromPath(Long datasetId, Path zipPath, java.util.function.IntConsumer progressCallback);

    DatasetImageUploadRespVO importZipFromPath(Long datasetId, Path zipPath,
                                               java.util.function.IntConsumer progressCallback,
                                               ImportCancelChecker cancelChecker);
}
