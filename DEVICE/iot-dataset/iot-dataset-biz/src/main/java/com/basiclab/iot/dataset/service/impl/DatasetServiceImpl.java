package com.basiclab.iot.dataset.service.impl;

import com.basiclab.iot.common.domain.PageResult;
import com.basiclab.iot.common.enums.CommonStatusEnum;
import com.basiclab.iot.common.utils.UUIDUtil;
import com.basiclab.iot.common.utils.object.BeanUtils;
import com.basiclab.iot.dataset.dal.dataobject.DatasetDO;
import com.basiclab.iot.dataset.dal.pgsql.DatasetMapper;
import com.basiclab.iot.dataset.domain.dataset.vo.AutoLabelModelReqVO;
import com.basiclab.iot.dataset.domain.dataset.vo.DatasetPageReqVO;
import com.basiclab.iot.dataset.domain.dataset.vo.DatasetSaveReqVO;
import com.basiclab.iot.dataset.domain.dataset.vo.DatasetSplitReqVO;
import com.basiclab.iot.dataset.enums.dataset.DatasetAudit;
import com.basiclab.iot.dataset.service.DatasetImageService;
import com.basiclab.iot.dataset.service.DatasetService;
import com.basiclab.iot.file.RemoteFileService;
import com.github.pagehelper.PageHelper;
import com.github.pagehelper.PageInfo;
import org.springframework.stereotype.Service;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.multipart.MultipartFile;

import javax.annotation.Resource;
import java.math.BigDecimal;
import java.util.List;
import java.util.Objects;

import static com.basiclab.iot.common.exception.util.ServiceExceptionUtil.exception;
import static com.basiclab.iot.dataset.enums.ErrorCodeConstants.*;

/**
 * 数据集 Service 实现类
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Service
@Validated
public class DatasetServiceImpl implements DatasetService {

    @Resource
    private DatasetMapper datasetMapper;

    @Resource
    private DatasetImageService datasetImageService;

    @Resource
    private RemoteFileService remoteFileService;

    @Override
    public Long createDataset(DatasetSaveReqVO createReqVO) {
        // 插入
        DatasetDO dataset = BeanUtils.toBean(createReqVO, DatasetDO.class);
        dataset.setDatasetCode(UUIDUtil.getUUID16());
        dataset.setAudit(DatasetAudit.PENDING_APPROVAL.getKey());
        datasetMapper.insert(dataset);
        // 返回
        return dataset.getId();
    }

    @Override
    public void updateDataset(DatasetSaveReqVO updateReqVO) {
        // 校验存在
        validateExists(updateReqVO.getId());
        // 更新
        DatasetDO updateObj = BeanUtils.toBean(updateReqVO, DatasetDO.class);
        datasetMapper.updateById(updateObj);
    }

    @Override
    public void deleteDataset(Long id) {
        // 校验存在
        validateExists(id);
        // 删除
        datasetMapper.deleteById(id);
    }

    private void validateExists(Long id) {
        if (datasetMapper.selectById(id) == null) {
            throw exception(DATASET_NOT_EXISTS);
        }
    }

    @Override
    public DatasetDO getDataset(Long id) {
        return datasetMapper.getDataset(id);
    }

    @Override
    public PageInfo<DatasetDO> getDatasetPage(DatasetPageReqVO pageReqVO) {
        PageHelper.startPage(pageReqVO.getPageNo(), pageReqVO.getPageSize());
        List<DatasetDO> datasetDOList = datasetMapper.getDatasetList(pageReqVO);
        return new PageInfo<>(datasetDOList);
    }

    @Override
    public String uploadCover(MultipartFile file) throws Exception {
        return remoteFileService.upload(file).getData().getUrl();
    }

    @Override
    public void setAutoLabelModel(Long datasetId, AutoLabelModelReqVO reqVO) {
        // 1. 验证数据集存在
        validateExists(datasetId);

        // 3. 更新数据集状态
        datasetMapper.updateById(new DatasetDO().setId(datasetId)
                .setModelServiceId(reqVO.getModelServiceId()));
    }

    @Override
    public void autoLabelDataset(Long datasetId) {
        //TODO 此处为示例伪代码，实际实现需要根据具体模型服务进行适配
    }

    @Override
    public void splitDataset(Long datasetId, DatasetSplitReqVO splitReqVO) {
        // 验证比例总和为1
        if (splitReqVO.getTrainRatio().add(splitReqVO.getValRatio())
                .add(splitReqVO.getTestRatio()).compareTo(BigDecimal.ONE) != 0) {
            throw exception(DATASET_SPLIT_RATIO_INVALID);
        }

        // 验证数据集是否已经被划分
        if (Objects.equals(datasetMapper.selectById(datasetId).getIsAllocated(), CommonStatusEnum.YES.getStatus())) {
            throw exception(DATASET_ALLOCATED);
        }

        // 划分图像数据集比例
        datasetImageService.splitDataset(datasetId, splitReqVO.getTrainRatio(), splitReqVO.getValRatio(), splitReqVO.getTestRatio());
    }

    @Override
    public void resetDataset(Long datasetId) {
        // 1. 验证数据集存在
        validateExists(datasetId);

        // 划分图像数据集比例
        datasetImageService.resetUsageByDatasetId(datasetId);

        // 3. 更新数据集状态
        datasetMapper.updateById(new DatasetDO().setId(datasetId)
                .setIsAllocated(CommonStatusEnum.NO.getStatus()));
    }
}