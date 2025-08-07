package com.basiclab.iot.device.service.product_commands_requests;

import org.springframework.stereotype.Service;
import javax.annotation.Resource;
import org.springframework.validation.annotation.Validated;

import com.basiclab.iot.device.controller.admin.product_commands_requests.vo.*;
import com.basiclab.iot.device.dal.dataobject.product_commands_requests.ProductCommandsRequestsDO;
import com.basiclab.iot.common.domain.PageResult;
import com.basiclab.iot.common.utils.object.BeanUtils;

import com.basiclab.iot.device.dal.mysql.product_commands_requests.ProductCommandsRequestsMapper;

import static com.basiclab.iot.device.enums.ErrorCodeConstants.PRODUCT_COMMANDS_REQUESTS_NOT_EXISTS;
import static com.basiclab.iot.common.exception.util.ServiceExceptionUtil.exception;

/**
 * 产品模型设备下发服务命令属性 Service 实现类
 *
 * @author BasicLab
 */
@Service
@Validated
public class ProductCommandsRequestsServiceImpl implements ProductCommandsRequestsService {

    @Resource
    private ProductCommandsRequestsMapper commandsRequestsMapper;

    @Override
    public Long createCommandsRequests(ProductCommandsRequestsSaveReqVO createReqVO) {
        // 插入
        ProductCommandsRequestsDO commandsRequests = BeanUtils.toBean(createReqVO, ProductCommandsRequestsDO.class);
        commandsRequestsMapper.insert(commandsRequests);
        // 返回
        return commandsRequests.getId();
    }

    @Override
    public void updateCommandsRequests(ProductCommandsRequestsSaveReqVO updateReqVO) {
        // 校验存在
        validateCommandsRequestsExists(updateReqVO.getId());
        // 更新
        ProductCommandsRequestsDO updateObj = BeanUtils.toBean(updateReqVO, ProductCommandsRequestsDO.class);
        commandsRequestsMapper.updateById(updateObj);
    }

    @Override
    public void deleteCommandsRequests(Long id) {
        // 校验存在
        validateCommandsRequestsExists(id);
        // 删除
        commandsRequestsMapper.deleteById(id);
    }

    private void validateCommandsRequestsExists(Long id) {
        if (commandsRequestsMapper.selectById(id) == null) {
            throw exception(PRODUCT_COMMANDS_REQUESTS_NOT_EXISTS);
        }
    }

    @Override
    public ProductCommandsRequestsDO getCommandsRequests(Long id) {
        return commandsRequestsMapper.selectById(id);
    }

    @Override
    public PageResult<ProductCommandsRequestsDO> getCommandsRequestsPage(ProductCommandsRequestsPageReqVO pageReqVO) {
        return commandsRequestsMapper.selectPage(pageReqVO);
    }

}