package com.basiclab.iot.device.service.protocol;

import org.springframework.stereotype.Service;
import javax.annotation.Resource;
import org.springframework.validation.annotation.Validated;

import com.basiclab.iot.device.controller.admin.protocol.vo.*;
import com.basiclab.iot.device.dal.dataobject.protocol.ProtocolDO;
import com.basiclab.iot.common.domain.PageResult;
import com.basiclab.iot.common.utils.object.BeanUtils;

import com.basiclab.iot.device.dal.mysql.protocol.ProtocolMapper;

import static com.basiclab.iot.common.exception.util.ServiceExceptionUtil.exception;
import static com.basiclab.iot.device.enums.ErrorCodeConstants.*;

/**
 * 协议信息 Service 实现类
 *
 * @author BasicLab
 */
@Service
@Validated
public class ProtocolServiceImpl implements ProtocolService {

    @Resource
    private ProtocolMapper protocolMapper;

    @Override
    public Long create(ProtocolSaveReqVO createReqVO) {
        // 插入
        ProtocolDO protocolDO = BeanUtils.toBean(createReqVO, ProtocolDO.class);
        protocolMapper.insert(protocolDO);
        // 返回
        return protocolDO.getId();
    }

    @Override
    public void update(ProtocolSaveReqVO updateReqVO) {
        // 校验存在
        validateExists(updateReqVO.getId());
        // 更新
        ProtocolDO updateObj = BeanUtils.toBean(updateReqVO, ProtocolDO.class);
        protocolMapper.updateById(updateObj);
    }

    @Override
    public void delete(Long id) {
        // 校验存在
        validateExists(id);
        // 删除
        protocolMapper.deleteById(id);
    }

    private void validateExists(Long id) {
        if (protocolMapper.selectById(id) == null) {
            throw exception(PROTOCOL_NOT_EXISTS);
        }
    }

    @Override
    public ProtocolDO get(Long id) {
        return protocolMapper.selectById(id);
    }

    @Override
    public PageResult<ProtocolDO> getPage(ProtocolPageReqVO pageReqVO) {
        return protocolMapper.selectPage(pageReqVO);
    }

}