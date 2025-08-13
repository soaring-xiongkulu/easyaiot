package com.basiclab.iot.device.service.product.impl;

import com.basiclab.iot.common.constant.Constants;
import com.basiclab.iot.common.text.UUID;
import com.basiclab.iot.common.utils.bean.BeanUtils;
import com.basiclab.iot.device.domain.device.vo.ProductProperties;
import com.basiclab.iot.device.domain.device.vo.ProductServices;
import com.basiclab.iot.device.domain.device.vo.ProductTemplate;
import com.basiclab.iot.device.domain.product.model.ProductTemplateModel;
import com.basiclab.iot.device.domain.product.model.Properties;
import com.basiclab.iot.device.domain.product.model.Services;
import com.basiclab.iot.device.dal.pgsql.product.ProductTemplateMapper;
import com.basiclab.iot.device.service.product.ProductPropertiesService;
import com.basiclab.iot.device.service.product.ProductServicesService;
import com.basiclab.iot.device.service.product.ProductTemplateService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import javax.annotation.Resource;
import java.util.ArrayList;
import java.util.List;

/**
 * @author: EasyAIoT
 * @email: andywebjava@163.com
 */
@Service
public class ProductTemplateServiceImpl implements ProductTemplateService {

    @Resource
    private ProductTemplateMapper productTemplateMapper;
    @Autowired
    private ProductServicesService productServicesService;
    @Autowired
    private ProductPropertiesService productPropertiesService;

    @Override
    public int deleteByPrimaryKey(Long id) {
        return productTemplateMapper.deleteByPrimaryKey(id);
    }

    @Override
    public int insert(ProductTemplate record) {
        return productTemplateMapper.insert(record);
    }

    @Override
    public int insertOrUpdate(ProductTemplate record) {
        return productTemplateMapper.insertOrUpdate(record);
    }

    @Override
    public int insertOrUpdateSelective(ProductTemplate record) {
        return productTemplateMapper.insertOrUpdateSelective(record);
    }

    @Override
    public int insertSelective(ProductTemplate record) {
        return productTemplateMapper.insertSelective(record);
    }

    @Override
    public ProductTemplate selectByPrimaryKey(Long id) {
        return productTemplateMapper.selectByPrimaryKey(id);
    }

    @Override
    public int updateByPrimaryKeySelective(ProductTemplate record) {
        return productTemplateMapper.updateByPrimaryKeySelective(record);
    }

    @Override
    public int updateByPrimaryKey(ProductTemplate record) {
        return productTemplateMapper.updateByPrimaryKey(record);
    }

    @Override
    public int updateBatch(List<ProductTemplate> list) {
        return productTemplateMapper.updateBatch(list);
    }

    @Override
    public int updateBatchSelective(List<ProductTemplate> list) {
        return productTemplateMapper.updateBatchSelective(list);
    }

    @Override
    public int batchInsert(List<ProductTemplate> list) {
        return productTemplateMapper.batchInsert(list);
    }

    /**
     * 查询产品模板
     *
     * @param id 产品模板主键
     * @return 产品模板
     */
    @Override
    public ProductTemplate selectProductTemplateById(Long id) {
        return productTemplateMapper.selectProductTemplateById(id);
    }

    /**
     * 查询产品模板 带服务、属性
     *
     * @param id 产品模板主键
     * @return 产品模板
     */
    @Override
    public ProductTemplateModel selectFullProductTemplateById(Long id) {
        ProductTemplate productTemplate = selectProductTemplateById(id);
        ProductTemplateModel productTemplateModel = new ProductTemplateModel();
        if (productTemplate != null) {
            BeanUtils.copyBeanProp(productTemplateModel, productTemplate);
            ProductServices find = new ProductServices();
            find.setTemplateIdentification(productTemplate.getTemplateIdentification());
            find.setStatus(Constants.ENABLE);
            // 查询服务列表
            List<ProductServices> productServicesList = productServicesService.selectProductServicesList(find);
            if (!productServicesList.isEmpty()) {
                List<Services> services = new ArrayList<>();
                productServicesList.forEach(ps -> {
                    Services service = new Services();
                    BeanUtils.copyBeanProp(service, ps);
                    service.setServiceId(String.valueOf(ps.getId()));
                    // 查询服务属性列表
                    List<ProductProperties> productPropertiesList = productPropertiesService.findAllByServiceId(ps.getId());
                    if (!productPropertiesList.isEmpty()) {
                        List<Properties> properties = new ArrayList<>();
                        productPropertiesList.forEach(pp -> {
                            Properties p = new Properties();
                            BeanUtils.copyBeanProp(p, pp);
                            properties.add(p);
                        });
                        service.setProperties(properties);
                    }
                    services.add(service);
                });
                productTemplateModel.setServices(services);
            }
        }
        return productTemplateModel;
    }

    /**
     * 查询产品模板列表
     *
     * @param productTemplate 产品模板
     * @return 产品模板集合
     */
    @Override
    public List<ProductTemplate> selectProductTemplateList(ProductTemplate productTemplate) {
        return productTemplateMapper.selectProductTemplateList(productTemplate);
    }

    /**
     * 新增产品模板
     *
     * @param productTemplate 产品模板
     * @return 结果
     */
    @Override
    public int insertProductTemplate(ProductTemplate productTemplate) {
        productTemplate.setTemplateIdentification(UUID.getUUID());
        return productTemplateMapper.insertProductTemplate(productTemplate);
    }

    /**
     * 修改产品模板
     *
     * @param productTemplate 产品模板
     * @return 结果
     */
    @Override
    public int updateProductTemplate(ProductTemplate productTemplate) {
        return productTemplateMapper.updateProductTemplate(productTemplate);
    }

    /**
     * 批量删除产品模板
     *
     * @param ids 需要删除的产品模板主键集合
     * @return 结果
     */
    @Override
    public int deleteProductTemplateByIds(Long[] ids) {
        return productTemplateMapper.deleteProductTemplateByIds(ids);
    }

}



