package com.basiclab.iot.device.dal.pgsql.product;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.basiclab.iot.device.domain.device.vo.ProductEvent;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

import java.util.List;

/**
 * ProductEventMapper
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Mapper
public interface ProductEventMapper extends BaseMapper<ProductEvent> {

    /**
     * 根据ID查询
     *
     * @param id 主键ID
     * @return 产品事件
     */
    ProductEvent queryById(@Param("id") Long id);

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
    int insertBatch(@Param("entities") List<ProductEvent> entities);

    /**
     * 批量新增或更新
     *
     * @param entities 产品事件列表
     * @return 影响行数
     */
    int insertOrUpdateBatch(@Param("entities") List<ProductEvent> entities);

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
    int deleteById(@Param("ids") Long[] ids);
}
