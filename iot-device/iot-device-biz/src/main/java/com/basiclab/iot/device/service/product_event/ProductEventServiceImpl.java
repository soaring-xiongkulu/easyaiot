package com.basiclab.iot.device.service.product_event;

import org.springframework.stereotype.Service;
import javax.annotation.Resource;
import org.springframework.validation.annotation.Validated;

import com.basiclab.iot.device.controller.admin.product_event.vo.*;
import com.basiclab.iot.device.dal.dataobject.product_event.ProductEventDO;
import com.basiclab.iot.common.domain.PageResult;
import com.basiclab.iot.common.utils.object.BeanUtils;

import com.basiclab.iot.device.dal.mysql.product_event.ProductEventMapper;

import static com.basiclab.iot.device.enums.ErrorCodeConstants.PRODUCT_EVENT_NOT_EXISTS;
import static com.basiclab.iot.common.exception.util.ServiceExceptionUtil.exception;

/**
 * 产品模型事件 Service 实现类
 *
 * @author BasicLab
 */
@Service
@Validated
public class ProductEventServiceImpl implements ProductEventService {

    @Resource
    private ProductEventMapper eventMapper;

    @Override
    public Long createEvent(ProductEventSaveReqVO createReqVO) {
        // 插入
        ProductEventDO event = BeanUtils.toBean(createReqVO, ProductEventDO.class);
        eventMapper.insert(event);
        // 返回
        return event.getId();
    }

    @Override
    public void updateEvent(ProductEventSaveReqVO updateReqVO) {
        // 校验存在
        validateEventExists(updateReqVO.getId());
        // 更新
        ProductEventDO updateObj = BeanUtils.toBean(updateReqVO, ProductEventDO.class);
        eventMapper.updateById(updateObj);
    }

    @Override
    public void deleteEvent(Long id) {
        // 校验存在
        validateEventExists(id);
        // 删除
        eventMapper.deleteById(id);
    }

    private void validateEventExists(Long id) {
        if (eventMapper.selectById(id) == null) {
            throw exception(PRODUCT_EVENT_NOT_EXISTS);
        }
    }

    @Override
    public ProductEventDO getEvent(Long id) {
        return eventMapper.selectById(id);
    }

    @Override
    public PageResult<ProductEventDO> getEventPage(ProductEventPageReqVO pageReqVO) {
        return eventMapper.selectPage(pageReqVO);
    }

}