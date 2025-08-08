package com.basiclab.iot.device.service.product;

import com.basiclab.iot.device.domain.device.vo.ProductProperties;

import java.util.List;

/**
 * @author: EasyAIoT
 * @email: andywebjava@163.com
 */
public interface ProductPropertiesService {

    /**
     * 通过产品标识删除
     * @param templateIdentifications 产品标识列表
     */
    void deleteByTemplateIds(List<String> templateIdentifications);

    int deleteByPrimaryKey(Long id);

    int insert(ProductProperties record);

    int insertOrUpdate(ProductProperties record);

    int insertOrUpdateSelective(ProductProperties record);

    int insertSelective(ProductProperties record);

    ProductProperties selectByPrimaryKey(Long id);

    int updateByPrimaryKeySelective(ProductProperties record);

    int updateByPrimaryKey(ProductProperties record);

    int updateBatch(List<ProductProperties> list);

    int updateBatchSelective(List<ProductProperties> list);

    int batchInsert(List<ProductProperties> list);


    List<ProductProperties> findAllByServiceId(Long serviceId);

    /**
     * 查询产品模型服务属性
     *
     * @param id 产品模型服务属性主键
     * @return 产品模型服务属性
     */
    ProductProperties selectProductPropertiesById(Long id);

    /**
     * 查询产品模型服务属性列表
     *
     * @param productProperties 产品模型服务属性
     * @return 产品模型服务属性集合
     */
    List<ProductProperties> selectProductPropertiesList(ProductProperties productProperties);

    /**
     * 新增产品模型服务属性
     *
     * @param productProperties 产品模型服务属性
     * @return 结果
     */
    int insertProductProperties(ProductProperties productProperties);

    /**
     * 修改产品模型服务属性
     *
     * @param productProperties 产品模型服务属性
     * @return 结果
     */
    int updateProductProperties(ProductProperties productProperties);

    /**
     * 批量删除产品模型服务属性
     *
     * @param ids 需要删除的数据主键集合
     * @return 结果
     */
    int deleteProductPropertiesByIds(Long[] ids);

    List<ProductProperties> selectPropertiesByPropertiesIdList(List<Long> propertiesIdList);

    List<ProductProperties> selectPropertiesByServiceIdList(List<Long> serviceIdList);
}
