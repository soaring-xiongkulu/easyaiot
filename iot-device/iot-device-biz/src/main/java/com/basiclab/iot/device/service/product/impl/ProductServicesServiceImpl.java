package com.basiclab.iot.device.service.product.impl;

import com.basiclab.iot.device.domain.device.vo.ProductServices;
import com.basiclab.iot.device.dal.pgsql.product.ProductServicesMapper;
import com.basiclab.iot.device.service.product.ProductServicesService;
import org.springframework.stereotype.Service;

import javax.annotation.Resource;
import java.util.List;

/**
 * @author: EasyAIoT
 * @email: andywebjava@163.com
 */
@Service
public class ProductServicesServiceImpl implements ProductServicesService {

    @Resource
    private ProductServicesMapper productServicesMapper;

    @Override
    public void deleteByTemplateIds(List<String> templateIdentifications) {
        productServicesMapper.deleteByTemplateIds(templateIdentifications);
    }

    @Override
    public int deleteByPrimaryKey(Long id) {
        return productServicesMapper.deleteByPrimaryKey(id);
    }

    @Override
    public int insert(ProductServices record) {
        return productServicesMapper.insert(record);
    }

    @Override
    public int insertOrUpdate(ProductServices record) {
        return productServicesMapper.insertOrUpdate(record);
    }

    @Override
    public int insertOrUpdateSelective(ProductServices record) {
        return productServicesMapper.insertOrUpdateSelective(record);
    }

    @Override
    public int insertSelective(ProductServices record) {
        return productServicesMapper.insertSelective(record);
    }

    @Override
    public ProductServices selectByPrimaryKey(Long id) {
        return productServicesMapper.selectByPrimaryKey(id);
    }

    @Override
    public int updateByPrimaryKeySelective(ProductServices record) {
        return productServicesMapper.updateByPrimaryKeySelective(record);
    }

    @Override
    public int updateByPrimaryKey(ProductServices record) {
        return productServicesMapper.updateByPrimaryKey(record);
    }

    @Override
    public int updateBatch(List<ProductServices> list) {
        return productServicesMapper.updateBatch(list);
    }

    @Override
    public int updateBatchSelective(List<ProductServices> list) {
        return productServicesMapper.updateBatchSelective(list);
    }

    @Override
    public int batchInsert(List<ProductServices> list) {
        return productServicesMapper.batchInsert(list);
    }

    @Override
    public List<ProductServices> findByProductIdentifications(List<String> productIds) {
        return productServicesMapper.findByProductIdentifications(productIds);
    }

    @Override
    public List<ProductServices> findAllByProductIdentificationIdAndStatus(String productIdentification, String status) {
        return productServicesMapper.findAllByProductIdentificationIdAndStatus(productIdentification, status);
    }

    @Override
    public List<ProductServices> findAllByProductIdentificationAndServiceCodeAndStatus(String productIdentification, String serviceCode, String status) {
        return productServicesMapper.findAllByProductIdentificationAndServiceCodeAndStatus(productIdentification, serviceCode, status);
    }

    /**
     * 查询产品模型服务
     *
     * @param id 产品模型服务主键
     * @return 产品模型服务
     */
    @Override
    public ProductServices selectProductServicesById(Long id) {
        return productServicesMapper.selectProductServicesById(id);
    }

    /**
     * 查询产品模型服务列表
     *
     * @param productServices 产品模型服务
     * @return 产品模型服务
     */
    @Override
    public List<ProductServices> selectProductServicesList(ProductServices productServices) {
        return productServicesMapper.selectProductServicesList(productServices);
    }

    /**
     * 新增产品模型服务
     *
     * @param productServices 产品模型服务
     * @return 结果
     */
    @Override
    public int insertProductServices(ProductServices productServices) {
        return productServicesMapper.insertProductServices(productServices);
    }

    /**
     * 修改产品模型服务
     *
     * @param productServices 产品模型服务
     * @return 结果
     */
    @Override
    public int updateProductServices(ProductServices productServices) {
        return productServicesMapper.updateProductServices(productServices);
    }

    /**
     * 批量删除产品模型服务
     *
     * @param ids 需要删除的产品模型服务主键
     * @return 结果
     */
    @Override
    public int deleteProductServicesByIds(Long[] ids) {
        return productServicesMapper.deleteProductServicesByIds(ids);
    }


    /**
     * 根据产品标识和状态获取产品所有服务
     *
     * @param productIdentification
     * @param status
     * @return
     */
    @Override
    public List<ProductServices> selectAllByProductIdentificationAndStatus(String productIdentification, String status) {
        return productServicesMapper.selectAllByProductIdentificationAndStatus(productIdentification, status);
    }

    @Override
    public List<ProductServices> selectProductServicesByIdList(List<Long> serviceIdList){
        return productServicesMapper.selectProductServicesByIdList( serviceIdList);
    }
}

