package com.basiclab.iot.device.service.product_commands;

import org.springframework.stereotype.Service;
import javax.annotation.Resource;
import org.springframework.validation.annotation.Validated;

import com.basiclab.iot.device.controller.admin.product_commands.vo.*;
import com.basiclab.iot.device.dal.dataobject.product_commands.ProductCommandsDO;
import com.basiclab.iot.common.domain.PageResult;
import com.basiclab.iot.common.utils.object.BeanUtils;

import com.basiclab.iot.device.dal.mysql.product_commands.ProductCommandsMapper;

import static com.basiclab.iot.device.enums.ErrorCodeConstants.PRODUCT_COMMANDS_NOT_EXISTS;
import static com.basiclab.iot.common.exception.util.ServiceExceptionUtil.exception;

/**
 * 产品模型设备服务命令 Service 实现类
 *
 * @author BasicLab
 */
@Service
@Validated
public class ProductCommandsServiceImpl implements ProductCommandsService {

    @Resource
    private ProductCommandsMapper commandsMapper;

    @Override
    public Long createCommands(ProductCommandsSaveReqVO createReqVO) {
        // 插入
        ProductCommandsDO commands = BeanUtils.toBean(createReqVO, ProductCommandsDO.class);
        commandsMapper.insert(commands);
        // 返回
        return commands.getId();
    }

    @Override
    public void updateCommands(ProductCommandsSaveReqVO updateReqVO) {
        // 校验存在
        validateCommandsExists(updateReqVO.getId());
        // 更新
        ProductCommandsDO updateObj = BeanUtils.toBean(updateReqVO, ProductCommandsDO.class);
        commandsMapper.updateById(updateObj);
    }

    @Override
    public void deleteCommands(Long id) {
        // 校验存在
        validateCommandsExists(id);
        // 删除
        commandsMapper.deleteById(id);
    }

    private void validateCommandsExists(Long id) {
        if (commandsMapper.selectById(id) == null) {
            throw exception(PRODUCT_COMMANDS_NOT_EXISTS);
        }
    }

    @Override
    public ProductCommandsDO getCommands(Long id) {
        return commandsMapper.selectById(id);
    }

    @Override
    public PageResult<ProductCommandsDO> getCommandsPage(ProductCommandsPageReqVO pageReqVO) {
        return commandsMapper.selectPage(pageReqVO);
    }

}