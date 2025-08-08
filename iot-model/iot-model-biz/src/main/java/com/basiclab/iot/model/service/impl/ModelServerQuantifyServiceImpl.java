package com.basiclab.iot.model.service.impl;

import com.basiclab.iot.common.domain.PageResult;
import com.basiclab.iot.common.utils.object.BeanUtils;
import com.basiclab.iot.model.dal.dataobject.ModelServerQuantifyDO;
import com.basiclab.iot.model.dal.pgsql.ModelServerQuantifyMapper;
import com.basiclab.iot.model.domain.model.vo.ModelServerQuantifyPageReqVO;
import com.basiclab.iot.model.domain.model.vo.ModelServerQuantifySaveReqVO;
import com.basiclab.iot.model.service.ModelServerQuantifyService;
import org.springframework.stereotype.Service;
import org.springframework.validation.annotation.Validated;

import javax.annotation.Resource;

import static com.basiclab.iot.common.exception.util.ServiceExceptionUtil.exception;
import static com.basiclab.iot.model.enums.ErrorCodeConstants.MODEL_SERVER_QUANTIFY_NOT_EXISTS;

/**
 * 模型量化服务 Service 实现类
 *
 * @author EasyAIoT
 */
@Service
@Validated
public class ModelServerQuantifyServiceImpl implements ModelServerQuantifyService {

    @Resource
    private ModelServerQuantifyMapper modelServerQuantifyMapper;

    @Override
    public Long createServerQuantify(ModelServerQuantifySaveReqVO createReqVO) {
        // 插入
        ModelServerQuantifyDO serverQuantify = BeanUtils.toBean(createReqVO, ModelServerQuantifyDO.class);
        modelServerQuantifyMapper.insert(serverQuantify);
        // 返回
        return serverQuantify.getId();
    }

    @Override
    public void updateServerQuantify(ModelServerQuantifySaveReqVO updateReqVO) {
        // 校验存在
        validateServerQuantifyExists(updateReqVO.getId());
        // 更新
        ModelServerQuantifyDO updateObj = BeanUtils.toBean(updateReqVO, ModelServerQuantifyDO.class);
        modelServerQuantifyMapper.updateById(updateObj);
    }

    @Override
    public void deleteServerQuantify(Long id) {
        // 校验存在
        validateServerQuantifyExists(id);
        // 删除
        modelServerQuantifyMapper.deleteById(id);
    }

    private void validateServerQuantifyExists(Long id) {
        if (modelServerQuantifyMapper.selectById(id) == null) {
            throw exception(MODEL_SERVER_QUANTIFY_NOT_EXISTS);
        }
    }

    @Override
    public ModelServerQuantifyDO getServerQuantify(Long id) {
        return modelServerQuantifyMapper.selectById(id);
    }

    @Override
    public PageResult<ModelServerQuantifyDO> getServerQuantifyPage(ModelServerQuantifyPageReqVO pageReqVO) {
        return modelServerQuantifyMapper.selectPage(pageReqVO);
    }

}