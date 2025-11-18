package com.basiclab.iot.device.service.product;

import java.util.List;

import com.basiclab.iot.device.domain.device.vo.ProductCommandsRequests;
import org.apache.ibatis.annotations.Param;

/**
 * ProductCommandsRequestsService
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
public interface ProductCommandsRequestsService {

    int deleteByPrimaryKey(Long id);

    int insert(ProductCommandsRequests record);

    int insertOrUpdate(ProductCommandsRequests record);

    int insertOrUpdateSelective(ProductCommandsRequests record);

    int insertSelective(ProductCommandsRequests record);

    ProductCommandsRequests selectByPrimaryKey(Long id);

    int updateByPrimaryKeySelective(ProductCommandsRequests record);

    int updateByPrimaryKey(ProductCommandsRequests record);

    int updateBatch(List<ProductCommandsRequests> list);

    int updateBatchSelective(List<ProductCommandsRequests> list);

    int batchInsert(List<ProductCommandsRequests> list);

    /**
     * 查询产品模型设备下发服务命令属性
     *
     * @param id 产品模型设备下发服务命令属性主键
     * @return 产品模型设备下发服务命令属性
     */
    ProductCommandsRequests selectProductCommandsRequestsById(Long id);

    /**
     * 查询产品模型设备下发服务命令属性列表
     *
     * @param productCommandsRequests 产品模型设备下发服务命令属性
     * @return 产品模型设备下发服务命令属性集合
     */
    List<ProductCommandsRequests> selectProductCommandsRequestsList(ProductCommandsRequests productCommandsRequests);

    /**
     * 新增产品模型设备下发服务命令属性
     *
     * @param productCommandsRequests 产品模型设备下发服务命令属性
     * @return 结果
     */
    int insertProductCommandsRequests(ProductCommandsRequests productCommandsRequests);

    /**
     * 修改产品模型设备下发服务命令属性
     *
     * @param productCommandsRequests 产品模型设备下发服务命令属性
     * @return 结果
     */
    int updateProductCommandsRequests(ProductCommandsRequests productCommandsRequests);

    /**
     * 批量删除产品模型设备下发服务命令属性
     *
     * @param ids 需要删除的产品模型设备下发服务命令属性主键集合
     * @return 结果
     */
    int deleteProductCommandsRequestsByIds(Long[] ids);

    List<ProductCommandsRequests> selectProductCommandsRequestsByCommandIdList(@Param("commandIdList") List<Long> commandIdList);

}
