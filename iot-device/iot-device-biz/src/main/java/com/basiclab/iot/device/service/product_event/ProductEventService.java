package com.basiclab.iot.device.service.product_event;

import javax.validation.*;
import com.basiclab.iot.device.controller.admin.product_event.vo.*;
import com.basiclab.iot.device.dal.dataobject.product_event.ProductEventDO;
import com.basiclab.iot.common.domain.PageResult;

/**
 * 产品模型事件 Service 接口
 *
 * @author BasicLab
 */
public interface ProductEventService {

    /**
     * 创建产品模型事件
     *
     * @param createReqVO 创建信息
     * @return 编号
     */
    Long createEvent(@Valid ProductEventSaveReqVO createReqVO);

    /**
     * 更新产品模型事件
     *
     * @param updateReqVO 更新信息
     */
    void updateEvent(@Valid ProductEventSaveReqVO updateReqVO);

    /**
     * 删除产品模型事件
     *
     * @param id 编号
     */
    void deleteEvent(Long id);

    /**
     * 获得产品模型事件
     *
     * @param id 编号
     * @return 产品模型事件
     */
    ProductEventDO getEvent(Long id);

    /**
     * 获得产品模型事件分页
     *
     * @param pageReqVO 分页查询
     * @return 产品模型事件分页
     */
    PageResult<ProductEventDO> getEventPage(ProductEventPageReqVO pageReqVO);

}