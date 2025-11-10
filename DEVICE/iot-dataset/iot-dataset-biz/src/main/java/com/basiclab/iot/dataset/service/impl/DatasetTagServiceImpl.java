package com.basiclab.iot.dataset.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.toolkit.Wrappers;
import com.baomidou.mybatisplus.extension.toolkit.SqlHelper;
import com.basiclab.iot.common.domain.PageResult;
import com.basiclab.iot.common.utils.object.BeanUtils;
import com.basiclab.iot.dataset.dal.dataobject.DatasetImageDO;
import com.basiclab.iot.dataset.dal.dataobject.DatasetTagDO;
import com.basiclab.iot.dataset.dal.pgsql.DatasetImageMapper;
import com.basiclab.iot.dataset.dal.pgsql.DatasetTagMapper;
import com.basiclab.iot.dataset.domain.dataset.vo.DatasetTagPageReqVO;
import com.basiclab.iot.dataset.domain.dataset.vo.DatasetTagSaveReqVO;
import com.basiclab.iot.dataset.service.DatasetTagService;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.apache.ibatis.logging.Log;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;
import org.springframework.validation.annotation.Validated;

import javax.annotation.Resource;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

import static com.baomidou.mybatisplus.extension.toolkit.Db.saveOrUpdateBatch;
import static com.basiclab.iot.common.exception.util.ServiceExceptionUtil.exception;
import static com.basiclab.iot.dataset.enums.ErrorCodeConstants.DATASET_TAG_NOT_EXISTS;
import static com.basiclab.iot.dataset.enums.ErrorCodeConstants.DATASET_TAG_NUMBER_EXISTS;

/**
 * 数据集标签 Service 实现类
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Service
@Validated
public class DatasetTagServiceImpl implements DatasetTagService {

    @Resource
    private DatasetTagMapper tagMapper;
    @Resource
    private DatasetImageMapper datasetImageMapper;

    private static final Logger logger = LoggerFactory.getLogger(DatasetTagServiceImpl.class);

    @Override
    public Long createDatasetTag(DatasetTagSaveReqVO createReqVO) {
        // 在当前数据集ID，快捷键不能重复
        LambdaQueryWrapper<DatasetTagDO> wrapper = Wrappers.lambdaQuery();
        wrapper.eq(DatasetTagDO::getDatasetId, createReqVO.getDatasetId());
        wrapper.eq(DatasetTagDO::getShortcut, createReqVO.getShortcut());
        if (tagMapper.selectOne(wrapper) != null) {
            throw exception(DATASET_TAG_NUMBER_EXISTS);
        }
        // 插入
        DatasetTagDO tag = BeanUtils.toBean(createReqVO, DatasetTagDO.class);
        tagMapper.insert(tag);
        // 返回
        return tag.getId();
    }

    @Override
    public void updateDatasetTag(DatasetTagSaveReqVO updateReqVO) {
        // 校验标签存在性
        DatasetTagDO oldTag = validateDatasetTagExists(updateReqVO.getId());
        // 在当前数据集ID，快捷键不能重复
        LambdaQueryWrapper<DatasetTagDO> wrapper = Wrappers.lambdaQuery();
        wrapper.eq(DatasetTagDO::getDatasetId, updateReqVO.getDatasetId());
        wrapper.eq(DatasetTagDO::getShortcut, updateReqVO.getShortcut());
        DatasetTagDO datasetTagDO = tagMapper.selectOne(wrapper);
        if (datasetTagDO != null && !datasetTagDO.getId().equals(updateReqVO.getId())) {
            throw exception(DATASET_TAG_NUMBER_EXISTS);
        }
        // 更新
        DatasetTagDO updateObj = BeanUtils.toBean(updateReqVO, DatasetTagDO.class);
        tagMapper.updateById(updateObj);
        // 若标签索引变更，同步更新图片标注
        if (!oldTag.getShortcut().equals(updateReqVO.getShortcut())) {
            updateImageAnnotationsByTagId(updateReqVO.getDatasetId(), oldTag, updateReqVO);
        }
    }

    @Override
    public void deleteDatasetTag(Long id) {
        // 校验存在
        validateDatasetTagExists(id);
        // 删除
        tagMapper.deleteById(id);
    }

    @Override
    public DatasetTagDO getDatasetTag(Long id) {
        return tagMapper.selectById(id);
    }

    @Override
    public PageResult<DatasetTagDO> getDatasetTagPage(DatasetTagPageReqVO pageReqVO) {
        return tagMapper.selectPage(pageReqVO);
    }

    /**
     * 更新所有使用该标签的图片标注
     */
    private void updateImageAnnotationsByTagId(Long datasetId, DatasetTagDO oldTag, DatasetTagSaveReqVO newTag) {
        // 1. 仅查询必要字段（ID和标注内容）
        List<DatasetImageDO> images = datasetImageMapper.selectList(
                new LambdaQueryWrapper<DatasetImageDO>()
                        .eq(DatasetImageDO::getDatasetId, datasetId)
                        .isNotNull(DatasetImageDO::getAnnotations)
                        .select(DatasetImageDO::getId, DatasetImageDO::getAnnotations)
        );

        // 2. 并行处理JSON更新并过滤未变更记录
        List<DatasetImageDO> batchToUpdate = images.parallelStream()
                .map(image -> {
                    String updatedAnnotations = updateAnnotationsJson(
                            image.getAnnotations(),
                            oldTag.getShortcut(),
                            newTag.getShortcut()
                    );
                    if (!updatedAnnotations.equals(image.getAnnotations())) {
                        image.setAnnotations(updatedAnnotations);
                        return image;
                    }
                    return null;
                })
                .filter(image -> image != null)
                .collect(Collectors.toList());

        // 3. 使用 saveOrUpdateBatch 批量更新
        if (!batchToUpdate.isEmpty()) {
            // 分批次调用 saveOrUpdateBatch（每批500条）
            int batchSize = 500;
            for (int i = 0; i < batchToUpdate.size(); i += batchSize) {
                List<DatasetImageDO> subList = batchToUpdate.subList(i, Math.min(i + batchSize, batchToUpdate.size()));
                // 关键替换：直接调用 MyBatis-Plus 的批量方法
                saveOrUpdateBatch(subList, batchSize); // 自动判断主键是否存在并执行插入/更新
            }
        }
    }

    /**
     * 替换标注JSON中的标签信息
     */
    private String updateAnnotationsJson(String json, Integer oldTag, Integer newTag) {
        try {
            ObjectMapper mapper = new ObjectMapper();
            // 显式指定泛型类型
            List<Map<String, Object>> annotations = mapper.readValue(
                    json,
                    new TypeReference<List<Map<String, Object>>>() {
                    }
            );
            annotations.forEach(annotation -> {
                Object labelObj = annotation.get("label");
                if (labelObj != null && labelObj.toString().equals(oldTag.toString())) {
                    annotation.put("label", newTag);
                }
            });
            return mapper.writeValueAsString(annotations);
        } catch (JsonProcessingException e) {
            logger.error("标注JSON解析失败: {}", json, e);
            return json;
        }
    }

    // 修改原有校验方法以返回标签对象
    private DatasetTagDO validateDatasetTagExists(Long id) {
        DatasetTagDO tag = tagMapper.selectById(id);
        if (tag == null) throw exception(DATASET_TAG_NOT_EXISTS);
        return tag;
    }

}