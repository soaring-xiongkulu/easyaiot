package com.basiclab.iot.model.service.impl;

import com.basiclab.iot.common.domain.PageResult;
import com.basiclab.iot.common.utils.object.BeanUtils;
import com.basiclab.iot.model.dal.dataobject.ModelServerTestDO;
import com.basiclab.iot.model.dal.pgsql.ModelServerTestMapper;
import com.basiclab.iot.model.domain.model.vo.ModelServerTestPageReqVO;
import com.basiclab.iot.model.domain.model.vo.ModelServerTestSaveReqVO;
import com.basiclab.iot.model.service.ModelServerTestService;
import org.springframework.stereotype.Service;
import org.springframework.validation.annotation.Validated;

import javax.annotation.Resource;

import static com.basiclab.iot.common.exception.util.ServiceExceptionUtil.exception;
import static com.basiclab.iot.model.enums.ErrorCodeConstants.MODEL_SERVER_TEST_NOT_EXISTS;

/**
 * 模型测试服务 Service 实现类
 *
 * @author IoT
 */
@Service
@Validated
public class ModelServerTestServiceImpl implements ModelServerTestService {

    @Resource
    private ModelServerTestMapper modelServerTestMapper;

    @Override
    public Long createModelServerTest(ModelServerTestSaveReqVO createReqVO) {
        // 插入
        ModelServerTestDO serverTest = BeanUtils.toBean(createReqVO, ModelServerTestDO.class);
        modelServerTestMapper.insert(serverTest);
        // 返回
        return serverTest.getId();
    }

    @Override
    public void updateModelServerTest(ModelServerTestSaveReqVO updateReqVO) {
        // 校验存在
        validateModelServerTestExists(updateReqVO.getId());
        // 更新
        ModelServerTestDO updateObj = BeanUtils.toBean(updateReqVO, ModelServerTestDO.class);
        modelServerTestMapper.updateById(updateObj);
    }

    @Override
    public void deleteModelServerTest(Long id) {
        // 校验存在
        validateModelServerTestExists(id);
        // 删除
        modelServerTestMapper.deleteById(id);
    }

    private void validateModelServerTestExists(Long id) {
        if (modelServerTestMapper.selectById(id) == null) {
            throw exception(MODEL_SERVER_TEST_NOT_EXISTS);
        }
    }

    @Override
    public ModelServerTestDO getModelServerTest(Long id) {
        return modelServerTestMapper.selectById(id);
    }

    @Override
    public PageResult<ModelServerTestDO> getModelServerTestPage(ModelServerTestPageReqVO pageReqVO) {
        return modelServerTestMapper.selectPage(pageReqVO);
    }

}