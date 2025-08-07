package com.basiclab.iot.device.service.product_event_response;

import javax.validation.*;
import com.basiclab.iot.device.controller.admin.product_event_response.vo.*;
import com.basiclab.iot.device.dal.dataobject.product_event_response.ProductEventResponseDO;
import com.basiclab.iot.common.domain.PageResult;

/**
 * 产品模型事件响应 Service 接口
 *
 * @author BasicLab
 */
public interface ProductEventResponseService {

    /**
     * 创建产品模型事件响应
     *
     * @param createReqVO 创建信息
     * @return 编号
     */
    Long createEventResponse(@Valid ProductEventResponseSaveReqVO createReqVO);

    /**
     * 更新产品模型事件响应
     *
     * @param updateReqVO 更新信息
     */
    void updateEventResponse(@Valid ProductEventResponseSaveReqVO updateReqVO);

    /**
     * 删除产品模型事件响应
     *
     * @param id 编号
     */
    void deleteEventResponse(Long id);

    /**
     * 获得产品模型事件响应
     *
     * @param id 编号
     * @return 产品模型事件响应
     */
    ProductEventResponseDO getEventResponse(Long id);

    /**
     * 获得产品模型事件响应分页
     *
     * @param pageReqVO 分页查询
     * @return 产品模型事件响应分页
     */
    PageResult<ProductEventResponseDO> getEventResponsePage(ProductEventResponsePageReqVO pageReqVO);

}