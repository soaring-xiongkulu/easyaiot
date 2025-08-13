package com.basiclab.iot.model.service.impl;

import com.basiclab.iot.common.domain.PageResult;
import com.basiclab.iot.common.utils.object.BeanUtils;
import com.basiclab.iot.model.dal.dataobject.ModelServerDO;
import com.basiclab.iot.model.dal.pgsql.ModelServerMapper;
import com.basiclab.iot.model.domain.model.vo.ModelServerPageReqVO;
import com.basiclab.iot.model.domain.model.vo.ModelServerSaveReqVO;
import com.basiclab.iot.model.service.ModelServerService;
import org.springframework.stereotype.Service;
import org.springframework.validation.annotation.Validated;

import javax.annotation.Resource;

import static com.basiclab.iot.common.exception.util.ServiceExceptionUtil.exception;
import static com.basiclab.iot.model.enums.ErrorCodeConstants.MODEL_SERVER_NOT_EXISTS;

/**
 * 模型服务 Service 实现类
 *
 * @author EasyAIoT
 */
@Service
@Validated
public class ModelServerServiceImpl implements ModelServerService {

    @Resource
    private ModelServerMapper modelServerMapper;

    @Override
    public Long createServer(ModelServerSaveReqVO createReqVO) {
        // 插入
        ModelServerDO server = BeanUtils.toBean(createReqVO, ModelServerDO.class);
        modelServerMapper.insert(server);
        // 返回
        return server.getId();
    }

    @Override
    public void updateServer(ModelServerSaveReqVO updateReqVO) {
        // 校验存在
        validateServerExists(updateReqVO.getId());
        // 更新
        ModelServerDO updateObj = BeanUtils.toBean(updateReqVO, ModelServerDO.class);
        modelServerMapper.updateById(updateObj);
    }

    @Override
    public void deleteServer(Long id) {
        // 校验存在
        validateServerExists(id);
        // 删除
        modelServerMapper.deleteById(id);
    }

    private void validateServerExists(Long id) {
        if (modelServerMapper.selectById(id) == null) {
            throw exception(MODEL_SERVER_NOT_EXISTS);
        }
    }

    @Override
    public ModelServerDO getServer(Long id) {
        return modelServerMapper.selectById(id);
    }

    @Override
    public PageResult<ModelServerDO> getServerPage(ModelServerPageReqVO pageReqVO) {
        return modelServerMapper.selectPage(pageReqVO);
    }

}