package com.basiclab.iot.device.service.product_commands_response;

import org.springframework.stereotype.Service;
import javax.annotation.Resource;
import org.springframework.validation.annotation.Validated;

import com.basiclab.iot.device.controller.admin.product_commands_response.vo.*;
import com.basiclab.iot.device.dal.dataobject.product_commands_response.ProductCommandsResponseDO;
import com.basiclab.iot.common.domain.PageResult;
import com.basiclab.iot.common.utils.object.BeanUtils;

import com.basiclab.iot.device.dal.mysql.product_commands_response.ProductCommandsResponseMapper;

import static com.basiclab.iot.device.enums.ErrorCodeConstants.PRODUCT_COMMANDS_RESPONSE_NOT_EXISTS;
import static com.basiclab.iot.common.exception.util.ServiceExceptionUtil.exception;

/**
 * 产品模型设备响应服务命令属性 Service 实现类
 *
 * @author BasicLab
 */
@Service
@Validated
public class ProductCommandsResponseServiceImpl implements ProductCommandsResponseService {

    @Resource
    private ProductCommandsResponseMapper commandsResponseMapper;

    @Override
    public Long createCommandsResponse(ProductCommandsResponseSaveReqVO createReqVO) {
        // 插入
        ProductCommandsResponseDO commandsResponse = BeanUtils.toBean(createReqVO, ProductCommandsResponseDO.class);
        commandsResponseMapper.insert(commandsResponse);
        // 返回
        return commandsResponse.getId();
    }

    @Override
    public void updateCommandsResponse(ProductCommandsResponseSaveReqVO updateReqVO) {
        // 校验存在
        validateCommandsResponseExists(updateReqVO.getId());
        // 更新
        ProductCommandsResponseDO updateObj = BeanUtils.toBean(updateReqVO, ProductCommandsResponseDO.class);
        commandsResponseMapper.updateById(updateObj);
    }

    @Override
    public void deleteCommandsResponse(Long id) {
        // 校验存在
        validateCommandsResponseExists(id);
        // 删除
        commandsResponseMapper.deleteById(id);
    }

    private void validateCommandsResponseExists(Long id) {
        if (commandsResponseMapper.selectById(id) == null) {
            throw exception(PRODUCT_COMMANDS_RESPONSE_NOT_EXISTS);
        }
    }

    @Override
    public ProductCommandsResponseDO getCommandsResponse(Long id) {
        return commandsResponseMapper.selectById(id);
    }

    @Override
    public PageResult<ProductCommandsResponseDO> getCommandsResponsePage(ProductCommandsResponsePageReqVO pageReqVO) {
        return commandsResponseMapper.selectPage(pageReqVO);
    }

}