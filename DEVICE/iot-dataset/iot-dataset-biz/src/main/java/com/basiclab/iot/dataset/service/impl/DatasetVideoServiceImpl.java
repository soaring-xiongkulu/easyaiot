package com.basiclab.iot.dataset.service.impl;

import com.basiclab.iot.common.domain.PageResult;
import com.basiclab.iot.common.utils.object.BeanUtils;
import com.basiclab.iot.dataset.dal.dataobject.DatasetVideoDO;
import com.basiclab.iot.dataset.dal.pgsql.DatasetVideoMapper;
import com.basiclab.iot.dataset.domain.dataset.vo.DatasetVideoPageReqVO;
import com.basiclab.iot.dataset.domain.dataset.vo.DatasetVideoSaveReqVO;
import com.basiclab.iot.dataset.service.DatasetVideoService;
import org.springframework.stereotype.Service;
import org.springframework.validation.annotation.Validated;

import javax.annotation.Resource;

import static com.basiclab.iot.common.exception.util.ServiceExceptionUtil.exception;
import static com.basiclab.iot.dataset.enums.ErrorCodeConstants.DATASET_VIDEO_NOT_EXISTS;

/**
 * 视频数据集 Service 实现类
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Service
@Validated
public class DatasetVideoServiceImpl implements DatasetVideoService {

    @Resource
    private DatasetVideoMapper videoMapper;

    @Override
    public Long createDatasetVideo(DatasetVideoSaveReqVO createReqVO) {
        // 插入
        DatasetVideoDO video = BeanUtils.toBean(createReqVO, DatasetVideoDO.class);
        videoMapper.insert(video);
        // 返回
        return video.getId();
    }

    @Override
    public void updateDatasetVideo(DatasetVideoSaveReqVO updateReqVO) {
        // 校验存在
        validateDatasetVideoExists(updateReqVO.getId());
        // 更新
        DatasetVideoDO updateObj = BeanUtils.toBean(updateReqVO, DatasetVideoDO.class);
        videoMapper.updateById(updateObj);
    }

    @Override
    public void deleteDatasetVideo(Long id) {
        // 校验存在
        validateDatasetVideoExists(id);
        // 删除
        videoMapper.deleteById(id);
    }

    private void validateDatasetVideoExists(Long id) {
        if (videoMapper.selectById(id) == null) {
            throw exception(DATASET_VIDEO_NOT_EXISTS);
        }
    }

    @Override
    public DatasetVideoDO getDatasetVideo(Long id) {
        return videoMapper.selectById(id);
    }

    @Override
    public PageResult<DatasetVideoDO> getDatasetVideoPage(DatasetVideoPageReqVO pageReqVO) {
        return videoMapper.selectPage(pageReqVO);
    }

}