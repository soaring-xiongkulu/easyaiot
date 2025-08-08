package com.basiclab.iot.device.service.product.impl;

import org.springframework.stereotype.Service;

import javax.annotation.Resource;
import java.util.List;

import com.basiclab.iot.device.dal.pgsql.product.ProductPropertiesMapper;
import com.basiclab.iot.device.domain.device.vo.ProductProperties;
import com.basiclab.iot.device.service.product.ProductPropertiesService;

/**
 * @author: EasyAIoT
 * @email: andywebjava@163.com
 */
@Service
public class ProductPropertiesServiceImpl implements ProductPropertiesService {

    @Resource
    private ProductPropertiesMapper productPropertiesMapper;

    @Override
    public void deleteByTemplateIds(List<String> templateIdentifications) {
        productPropertiesMapper.deleteByTemplateIds(templateIdentifications);
    }

    @Override
    public int deleteByPrimaryKey(Long id) {
        return productPropertiesMapper.deleteByPrimaryKey(id);
    }

    @Override
    public int insert(ProductProperties record) {
        return productPropertiesMapper.insert(record);
    }

    @Override
    public int insertOrUpdate(ProductProperties record) {
        return productPropertiesMapper.insertOrUpdate(record);
    }

    @Override
    public int insertOrUpdateSelective(ProductProperties record) {
        return productPropertiesMapper.insertOrUpdateSelective(record);
    }

    @Override
    public int insertSelective(ProductProperties record) {
        return productPropertiesMapper.insertSelective(record);
    }

    @Override
    public ProductProperties selectByPrimaryKey(Long id) {
        return productPropertiesMapper.selectByPrimaryKey(id);
    }

    @Override
    public int updateByPrimaryKeySelective(ProductProperties record) {
        return productPropertiesMapper.updateByPrimaryKeySelective(record);
    }

    @Override
    public int updateByPrimaryKey(ProductProperties record) {
        return productPropertiesMapper.updateByPrimaryKey(record);
    }

    @Override
    public int updateBatch(List<ProductProperties> list) {
        return productPropertiesMapper.updateBatch(list);
    }

    @Override
    public int updateBatchSelective(List<ProductProperties> list) {
        return productPropertiesMapper.updateBatchSelective(list);
    }

    @Override
    public int batchInsert(List<ProductProperties> list) {
        return productPropertiesMapper.batchInsert(list);
    }

    @Override
    public List<ProductProperties> findAllByServiceId(Long serviceId) {
        return productPropertiesMapper.findAllByServiceId(serviceId);
    }

    /**
     * 查询产品模型服务属性
     *
     * @param id 产品模型服务属性主键
     * @return 产品模型服务属性
     */
    @Override
    public ProductProperties selectProductPropertiesById(Long id) {
        return productPropertiesMapper.selectProductPropertiesById(id);
    }

    /**
     * 查询产品模型服务属性列表
     *
     * @param productProperties 产品模型服务属性
     * @return 产品模型服务属性
     */
    @Override
    public List<ProductProperties> selectProductPropertiesList(ProductProperties productProperties) {
        return productPropertiesMapper.selectProductPropertiesList(productProperties);
    }

    /**
     * 新增产品模型服务属性
     *
     * @param productProperties 产品模型服务属性
     * @return 结果
     */
    @Override
    public int insertProductProperties(ProductProperties productProperties) {
        return productPropertiesMapper.insertProductProperties(productProperties);
    }

    /**
     * 修改产品模型服务属性
     *
     * @param productProperties 产品模型服务属性
     * @return 结果
     */
    @Override
    public int updateProductProperties(ProductProperties productProperties) {
        return productPropertiesMapper.updateProductProperties(productProperties);
    }

    /**
     * 批量删除产品模型服务属性
     *
     * @param ids 需要删除的产品模型服务属性主键
     * @return 结果
     */
    @Override
    public int deleteProductPropertiesByIds(Long[] ids) {
        return productPropertiesMapper.deleteProductPropertiesByIds(ids);
    }

    @Override
    public List<ProductProperties> selectPropertiesByPropertiesIdList(List<Long> propertiesIdList)
    {
        return productPropertiesMapper.selectPropertiesByPropertiesIdList(propertiesIdList);
    }

    @Override
    public List<ProductProperties> selectPropertiesByServiceIdList(List<Long> serviceIdList) {
        return productPropertiesMapper.selectPropertiesByServiceIdList(serviceIdList);
    }
}
