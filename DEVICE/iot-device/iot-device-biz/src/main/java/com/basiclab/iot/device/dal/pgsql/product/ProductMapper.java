package com.basiclab.iot.device.dal.pgsql.product;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.basiclab.iot.common.core.aop.TenantIgnore;
import com.basiclab.iot.device.domain.device.vo.Product;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

import java.util.List;

/**
 * ProductMapper
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Mapper
public interface ProductMapper extends BaseMapper<Product> {
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
    int insert(Product record);

    int insertOrUpdate(Product record);

    int insertOrUpdateSelective(Product record);

    /**
     * insert record to table selective
     *
     * @param record the record
     * @return insert count
     */
    int insertSelective(Product record);

    /**
     * select by primary key
     *
     * @param id primary key
     * @return object by primary key
     */
    Product selectByPrimaryKey(Long id);

    /**
     * update record selective
     *
     * @param record the updated record
     * @return update count
     */
    int updateByPrimaryKeySelective(Product record);

    /**
     * update record
     *
     * @param record the updated record
     * @return update count
     */
    int updateByPrimaryKey(Product record);

    int updateBatch(List<Product> list);

    int updateBatchSelective(List<Product> list);

    int batchInsert(@Param("list") List<Product> list);

    /**
     * 查询产品管理
     *
     * @param id 产品管理主键
     * @return 产品管理
     */
    Product selectProductById(Long id);

    /**
     * 查询产品管理
     *
     * @param productIdentification 产品标识
     * @return 产品管理
     */
    @TenantIgnore
    Product selectByProductIdentification(String productIdentification);

    /**
     * 查询产品管理列表
     *
     * @param product 产品管理
     * @return 产品管理集合
     */
    List<Product> selectProductList(Product product);

    /**
     * 新增产品管理
     *
     * @param product 产品管理
     * @return 结果
     */
    int insertProduct(Product product);

    /**
     * 修改产品管理
     *
     * @param product 产品管理
     * @return 结果
     */
    int updateProduct(Product product);

    /**
     * 删除产品管理
     *
     * @param id 产品管理主键
     * @return 结果
     */
    int deleteProductById(Long id);

    /**
     * 批量删除产品管理
     *
     * @param ids 需要删除的数据主键集合
     * @return 结果
     */
    int deleteProductByIds(Long[] ids);

    Product findOneByProductName(@Param("productName") String productName);

    List<Product> selectByManufacturerIdAndModelAndDeviceType(@Param("manufacturerId") String manufacturerId, @Param("model") String model, @Param("deviceType") String deviceType);

    Product findOneByManufacturerIdAndModelAndDeviceType(@Param("manufacturerId") String manufacturerId, @Param("model") String model, @Param("deviceType") String deviceType);

    List<Product> findAllByStatus(@Param("status") String status);

    Product findOneByManufacturerIdAndModelAndProtocolTypeAndStatus(@Param("manufacturerId") String manufacturerId, @Param("model") String model, @Param("protocolType") String protocolType, @Param("status") String status);

    Product findOneByIdAndStatus(@Param("id") Long id, @Param("status") String status);

    Product findOneByProductIdentificationAndProtocolType(@Param("productIdentification") String productIdentification);

    List<Product> findAllByIdInAndStatus(@Param("ids") List<Long> ids, @Param("status") String status);

    List<Product> selectAllProductByStatus(@Param("status") String status);

    List<Product> selectProductByProductIdentificationList(@Param("productIdentificationList") List<String> productIdentificationList);

    Long findProductTotal();

    List<Product> findProductsByPage(@Param("offset") int offset, @Param("pageSize") int pageSize);

    /**
     * 通过id查询标识，
     * @param ids id列表
     * @return 产品标识列表
     */
    List<String> selectIdentificationByIds(@Param("ids") Long[] ids);
}