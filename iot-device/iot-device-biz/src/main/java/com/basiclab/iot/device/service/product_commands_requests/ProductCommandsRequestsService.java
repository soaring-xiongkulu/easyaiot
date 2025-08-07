package com.basiclab.iot.device.service.product_commands_requests;

import javax.validation.*;
import com.basiclab.iot.device.controller.admin.product_commands_requests.vo.*;
import com.basiclab.iot.device.dal.dataobject.product_commands_requests.ProductCommandsRequestsDO;
import com.basiclab.iot.common.domain.PageResult;

/**
 * 产品模型设备下发服务命令属性 Service 接口
 *
 * @author BasicLab
 */
public interface ProductCommandsRequestsService {

    /**
     * 创建产品模型设备下发服务命令属性
     *
     * @param createReqVO 创建信息
     * @return 编号
     */
    Long createCommandsRequests(@Valid ProductCommandsRequestsSaveReqVO createReqVO);

    /**
     * 更新产品模型设备下发服务命令属性
     *
     * @param updateReqVO 更新信息
     */
    void updateCommandsRequests(@Valid ProductCommandsRequestsSaveReqVO updateReqVO);

    /**
     * 删除产品模型设备下发服务命令属性
     *
     * @param id 编号
     */
    void deleteCommandsRequests(Long id);

    /**
     * 获得产品模型设备下发服务命令属性
     *
     * @param id 编号
     * @return 产品模型设备下发服务命令属性
     */
    ProductCommandsRequestsDO getCommandsRequests(Long id);

    /**
     * 获得产品模型设备下发服务命令属性分页
     *
     * @param pageReqVO 分页查询
     * @return 产品模型设备下发服务命令属性分页
     */
    PageResult<ProductCommandsRequestsDO> getCommandsRequestsPage(ProductCommandsRequestsPageReqVO pageReqVO);

}