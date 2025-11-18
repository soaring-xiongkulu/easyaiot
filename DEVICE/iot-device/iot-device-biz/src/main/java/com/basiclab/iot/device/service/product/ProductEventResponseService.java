package com.basiclab.iot.device.service.product;

import com.baomidou.mybatisplus.extension.service.IService;
import com.basiclab.iot.device.domain.device.vo.ProductEventResponse;

import java.util.List;

/**
 * ProductEventResponseService
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
public interface ProductEventResponseService extends IService<ProductEventResponse> {

    /**
     * 根据ID查询
     *
     * @param id 主键ID
     * @return 产品事件响应
     */
    ProductEventResponse queryById(Long id);

    /**
     * 查询列表
     *
     * @param productEventResponse 查询条件
     * @return 产品事件响应列表
     */
    List<ProductEventResponse> selectList(ProductEventResponse productEventResponse);

    /**
     * 统计数量
     *
     * @param productEventResponse 查询条件
     * @return 数量
     */
    Long count(ProductEventResponse productEventResponse);

    /**
     * 新增
     *
     * @param productEventResponse 产品事件响应
     * @return 影响行数
     */
    int insert(ProductEventResponse productEventResponse);

    /**
     * 批量新增
     *
     * @param entities 产品事件响应列表
     * @return 影响行数
     */
    int insertBatch(List<ProductEventResponse> entities);

    /**
     * 批量新增或更新
     *
     * @param entities 产品事件响应列表
     * @return 影响行数
     */
    int insertOrUpdateBatch(List<ProductEventResponse> entities);

    /**
     * 更新
     *
     * @param productEventResponse 产品事件响应
     * @return 影响行数
     */
    int update(ProductEventResponse productEventResponse);

    /**
     * 根据ID删除
     *
     * @param ids ID列表
     * @return 影响行数
     */
    int deleteByIds(Long[] ids);
}

