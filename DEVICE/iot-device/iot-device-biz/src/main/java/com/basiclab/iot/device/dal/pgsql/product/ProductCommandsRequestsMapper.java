package com.basiclab.iot.device.dal.pgsql.product;

import com.basiclab.iot.device.domain.device.vo.ProductCommandsRequests;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

import java.util.List;

/**
 * ProductCommandsRequestsMapper
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Mapper
public interface ProductCommandsRequestsMapper {
    /**
     * delete by primary key
     *
     * @param id primaryKey
     * @return deleteCount
     */
    int deleteByPrimaryKey(Long id);

    /**
     * insert record to table
     *
     * @param record the record
     * @return insert count
     */
    int insert(ProductCommandsRequests record);

    int insertOrUpdate(ProductCommandsRequests record);

    int insertOrUpdateSelective(ProductCommandsRequests record);

    /**
     * insert record to table selective
     *
     * @param record the record
     * @return insert count
     */
    int insertSelective(ProductCommandsRequests record);

    /**
     * select by primary key
     *
     * @param id primary key
     * @return object by primary key
     */
    ProductCommandsRequests selectByPrimaryKey(Long id);

    /**
     * update record selective
     *
     * @param record the updated record
     * @return update count
     */
    int updateByPrimaryKeySelective(ProductCommandsRequests record);

    /**
     * update record
     *
     * @param record the updated record
     * @return update count
     */
    int updateByPrimaryKey(ProductCommandsRequests record);

    int updateBatch(List<ProductCommandsRequests> list);

    int updateBatchSelective(List<ProductCommandsRequests> list);

    int batchInsert(@Param("list") List<ProductCommandsRequests> list);

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
     * @param ids 需要删除的数据主键集合
     * @return 结果
     */
    int deleteProductCommandsRequestsByIds(Long[] ids);

    List<ProductCommandsRequests> selectProductCommandsRequestsByCommandIdList(@Param("commandIdList") List<Long> commandIdList);

}
