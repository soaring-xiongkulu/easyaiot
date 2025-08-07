package com.basiclab.iot.device.service.product_event_response;

import org.springframework.stereotype.Service;
import javax.annotation.Resource;
import org.springframework.validation.annotation.Validated;

import com.basiclab.iot.device.controller.admin.product_event_response.vo.*;
import com.basiclab.iot.device.dal.dataobject.product_event_response.ProductEventResponseDO;
import com.basiclab.iot.common.domain.PageResult;
import com.basiclab.iot.common.utils.object.BeanUtils;

import com.basiclab.iot.device.dal.mysql.product_event_response.ProductEventResponseMapper;

import static com.basiclab.iot.device.enums.ErrorCodeConstants.PRODUCT_EVENT_RESPONSE_NOT_EXISTS;
import static com.basiclab.iot.common.exception.util.ServiceExceptionUtil.exception;

/**
 * 产品模型事件响应 Service 实现类
 *
 * @author BasicLab
 */
@Service
@Validated
public class ProductEventResponseServiceImpl implements ProductEventResponseService {

    @Resource
    private ProductEventResponseMapper eventResponseMapper;

    @Override
    public Long createEventResponse(ProductEventResponseSaveReqVO createReqVO) {
        // 插入
        ProductEventResponseDO eventResponse = BeanUtils.toBean(createReqVO, ProductEventResponseDO.class);
        eventResponseMapper.insert(eventResponse);
        // 返回
        return eventResponse.getId();
    }

    @Override
    public void updateEventResponse(ProductEventResponseSaveReqVO updateReqVO) {
        // 校验存在
        validateEventResponseExists(updateReqVO.getId());
        // 更新
        ProductEventResponseDO updateObj = BeanUtils.toBean(updateReqVO, ProductEventResponseDO.class);
        eventResponseMapper.updateById(updateObj);
    }

    @Override
    public void deleteEventResponse(Long id) {
        // 校验存在
        validateEventResponseExists(id);
        // 删除
        eventResponseMapper.deleteById(id);
    }

    private void validateEventResponseExists(Long id) {
        if (eventResponseMapper.selectById(id) == null) {
            throw exception(PRODUCT_EVENT_RESPONSE_NOT_EXISTS);
        }
    }

    @Override
    public ProductEventResponseDO getEventResponse(Long id) {
        return eventResponseMapper.selectById(id);
    }

    @Override
    public PageResult<ProductEventResponseDO> getEventResponsePage(ProductEventResponsePageReqVO pageReqVO) {
        return eventResponseMapper.selectPage(pageReqVO);
    }

}