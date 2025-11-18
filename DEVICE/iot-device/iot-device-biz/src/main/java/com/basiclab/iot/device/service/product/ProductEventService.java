package com.basiclab.iot.device.service.product;

import com.baomidou.mybatisplus.extension.service.IService;
import com.basiclab.iot.device.domain.device.vo.ProductEvent;

import java.util.List;

/**
 * ProductEventService
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
public interface ProductEventService extends IService<ProductEvent> {

    /**
     * 根据ID查询
     *
     * @param id 主键ID
     * @return 产品事件
     */
    ProductEvent queryById(Long id);

    /**
     * 查询列表
     *
     * @param productEvent 查询条件
     * @return 产品事件列表
     */
    List<ProductEvent> selectList(ProductEvent productEvent);

    /**
     * 统计数量
     *
     * @param productEvent 查询条件
     * @return 数量
     */
    Long count(ProductEvent productEvent);

    /**
     * 新增
     *
     * @param productEvent 产品事件
     * @return 影响行数
     */
    int insert(ProductEvent productEvent);

    /**
     * 批量新增
     *
     * @param entities 产品事件列表
     * @return 影响行数
     */
    int insertBatch(List<ProductEvent> entities);

    /**
     * 批量新增或更新
     *
     * @param entities 产品事件列表
     * @return 影响行数
     */
    int insertOrUpdateBatch(List<ProductEvent> entities);

    /**
     * 更新
     *
     * @param productEvent 产品事件
     * @return 影响行数
     */
    int update(ProductEvent productEvent);

    /**
     * 根据ID删除
     *
     * @param ids ID列表
     * @return 影响行数
     */
    int deleteByIds(Long[] ids);
}

