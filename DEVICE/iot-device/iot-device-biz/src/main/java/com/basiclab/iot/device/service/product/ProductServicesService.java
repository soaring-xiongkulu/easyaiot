package com.basiclab.iot.device.service.product;

import com.basiclab.iot.device.domain.device.vo.ProductServices;

import java.util.List;

/**
 * ProductServicesService
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
public interface ProductServicesService {

    /**
     * 通过模板id删除服务
     *
     * @param ids 模板id列表
     */
    void deleteByTemplateIds(List<String> ids);

    int deleteByPrimaryKey(Long id);

    int insert(ProductServices record);

    int insertOrUpdate(ProductServices record);

    int insertOrUpdateSelective(ProductServices record);

    int insertSelective(ProductServices record);

    ProductServices selectByPrimaryKey(Long id);

    int updateByPrimaryKeySelective(ProductServices record);

    int updateByPrimaryKey(ProductServices record);

    int updateBatch(List<ProductServices> list);

    int updateBatchSelective(List<ProductServices> list);

    int batchInsert(List<ProductServices> list);

    List<ProductServices> findByProductIdentifications(List<String> productIdentifications);


    List<ProductServices> findAllByProductIdentificationIdAndStatus(String productIdentification, String status);


    List<ProductServices> findAllByProductIdentificationAndServiceCodeAndStatus(String productIdentification, String serviceCode, String status);

    /**
     * 查询产品模型服务
     *
     * @param id 产品模型服务主键
     * @return 产品模型服务
     */
    ProductServices selectProductServicesById(Long id);

    /**
     * 查询产品模型服务列表
     *
     * @param productServices 产品模型服务
     * @return 产品模型服务集合
     */
    List<ProductServices> selectProductServicesList(ProductServices productServices);

    /**
     * 新增产品模型服务
     *
     * @param productServices 产品模型服务
     * @return 结果
     */
    int insertProductServices(ProductServices productServices);

    /**
     * 修改产品模型服务
     *
     * @param productServices 产品模型服务
     * @return 结果
     */
    int updateProductServices(ProductServices productServices);

    /**
     * 批量删除产品模型服务
     *
     * @param ids 需要删除的产品模型服务主键集合
     * @return 结果
     */
    int deleteProductServicesByIds(Long[] ids);


    /**
     * 根据产品标识和状态获取产品所有服务
     * @param productIdentification
     * @param status
     * @return
     */
    List<ProductServices> selectAllByProductIdentificationAndStatus(String productIdentification, String status);

    List<ProductServices> selectProductServicesByIdList(List<Long> serviceIdList);
}

