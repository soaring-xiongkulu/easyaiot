package com.basiclab.iot.device.dal.pgsql.product;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.basiclab.iot.device.domain.device.vo.ProductEventResponse;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

import java.util.List;

/**
 * ProductEventResponseMapper
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Mapper
public interface ProductEventResponseMapper extends BaseMapper<ProductEventResponse> {

    /**
     * 根据ID查询
     *
     * @param id 主键ID
     * @return 产品事件响应
     */
    ProductEventResponse queryById(@Param("id") Long id);

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
    int insertBatch(@Param("entities") List<ProductEventResponse> entities);

    /**
     * 批量新增或更新
     *
     * @param entities 产品事件响应列表
     * @return 影响行数
     */
    int insertOrUpdateBatch(@Param("entities") List<ProductEventResponse> entities);

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
    int deleteByIds(@Param("ids") Long[] ids);
}
