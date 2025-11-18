package com.basiclab.iot.device.service.product;

import java.util.List;

import com.basiclab.iot.device.domain.device.vo.ProductCommandsResponse;
import org.apache.ibatis.annotations.Param;

/**
 * ProductCommandsResponseService
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
public interface ProductCommandsResponseService {

    int deleteByPrimaryKey(Long id);

    int insert(ProductCommandsResponse record);

    int insertOrUpdate(ProductCommandsResponse record);

    int insertOrUpdateSelective(ProductCommandsResponse record);

    int insertSelective(ProductCommandsResponse record);

    ProductCommandsResponse selectByPrimaryKey(Long id);

    int updateByPrimaryKeySelective(ProductCommandsResponse record);

    int updateByPrimaryKey(ProductCommandsResponse record);

    int updateBatch(List<ProductCommandsResponse> list);

    int updateBatchSelective(List<ProductCommandsResponse> list);

    int batchInsert(List<ProductCommandsResponse> list);

    /**
     * 查询产品模型设备响应服务命令属性
     *
     * @param id 产品模型设备响应服务命令属性主键
     * @return 产品模型设备响应服务命令属性
     */
    ProductCommandsResponse selectProductCommandsResponseById(Long id);

    /**
     * 查询产品模型设备响应服务命令属性列表
     *
     * @param productCommandsResponse 产品模型设备响应服务命令属性
     * @return 产品模型设备响应服务命令属性集合
     */
    List<ProductCommandsResponse> selectProductCommandsResponseList(ProductCommandsResponse productCommandsResponse);

    /**
     * 新增产品模型设备响应服务命令属性
     *
     * @param productCommandsResponse 产品模型设备响应服务命令属性
     * @return 结果
     */
    int insertProductCommandsResponse(ProductCommandsResponse productCommandsResponse);

    /**
     * 修改产品模型设备响应服务命令属性
     *
     * @param productCommandsResponse 产品模型设备响应服务命令属性
     * @return 结果
     */
    int updateProductCommandsResponse(ProductCommandsResponse productCommandsResponse);

    /**
     * 批量删除产品模型设备响应服务命令属性
     *
     * @param ids 需要删除的产品模型设备响应服务命令属性主键集合
     * @return 结果
     */
    int deleteProductCommandsResponseByIds(Long[] ids);

    List<ProductCommandsResponse> selectProductCommandsResponseByCommandIdList(@Param("commandIdList") List<Long> commandIdList);

}
