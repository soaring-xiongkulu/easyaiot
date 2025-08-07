package com.basiclab.iot.device.service.product_properties;

import com.basiclab.iot.device.controller.admin.product.ProductProperties;
import com.basiclab.iot.device.dal.mysql.product_properties.ProductPropertiesMapper;
import org.apache.logging.log4j.util.Strings;
import org.springframework.stereotype.Service;
import javax.annotation.Resource;
import org.springframework.validation.annotation.Validated;

import com.basiclab.iot.device.controller.admin.product_properties.vo.*;
import com.basiclab.iot.device.dal.dataobject.product_properties.ProductPropertiesDO;
import com.basiclab.iot.common.domain.PageResult;
import com.basiclab.iot.common.utils.object.BeanUtils;


import java.util.List;

import static com.basiclab.iot.device.enums.ErrorCodeConstants.PRODUCT_PROPERTIES_NOT_EXISTS;
import static com.basiclab.iot.common.exception.util.ServiceExceptionUtil.exception;

/**
 * 产品模型属性 Service 实现类
 *
 * @author BasicLab
 */
@Service
@Validated
public class ProductPropertiesServiceImpl implements ProductPropertiesService {
    @Resource
    private ProductPropertiesMapper productPropertiesMapper;

    /**
     * 产品模板标识
     */
    private static final Integer TEMPLATE_FLAG = 1;
    /**
     * 产品标识
     */
    private static final Integer PRODUCT_FLAG = 2;
    
    @Override
    public ProductProperties selectByPrimaryKey(Long id) {
        return productPropertiesMapper.selectByPrimaryKey(id);
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
        Boolean checked;
        if (Strings.isNotEmpty(productProperties.getProductIdentification())) {
            checked = checkPropertyCode(productProperties.getProductIdentification(), productProperties.getPropertyCode(), PRODUCT_FLAG);
        } else if (Strings.isNotEmpty(productProperties.getTemplateIdentification())) {
            checked = checkPropertyCode(productProperties.getTemplateIdentification(), productProperties.getPropertyCode(), TEMPLATE_FLAG);
        } else {
            throw new RuntimeException("产品标识和产品模板标识不能同时为空");
        }
        if (Boolean.TRUE.equals(checked)) {
            return productPropertiesMapper.insertProductProperties(productProperties);
        }
        return 0;
    }

    @Override
    public Boolean checkPropertyCode(String identification, String propertyCode, Integer flag) {
        Integer count = productPropertiesMapper.getByIdentificationAndPropertyCode(identification, propertyCode, flag);
        return count == 0;
    }

    @Override
    public Long createProperties(ProductPropertiesSaveReqVO createReqVO) {
        // 插入
        ProductPropertiesDO properties = BeanUtils.toBean(createReqVO, ProductPropertiesDO.class);
        productPropertiesMapper.insert(properties);
        // 返回
        return properties.getId();
    }

    @Override
    public void updateProperties(ProductPropertiesSaveReqVO updateReqVO) {
        // 校验存在
        validatePropertiesExists(updateReqVO.getId());
        // 更新
        ProductPropertiesDO updateObj = BeanUtils.toBean(updateReqVO, ProductPropertiesDO.class);
        productPropertiesMapper.updateById(updateObj);
    }

    @Override
    public void deleteProperties(Long id) {
        // 校验存在
        validatePropertiesExists(id);
        // 删除
        productPropertiesMapper.deleteById(id);
    }

    private void validatePropertiesExists(Long id) {
        if (productPropertiesMapper.selectById(id) == null) {
            throw exception(PRODUCT_PROPERTIES_NOT_EXISTS);
        }
    }

    @Override
    public ProductPropertiesDO getProperties(Long id) {
        return productPropertiesMapper.selectById(id);
    }

    @Override
    public PageResult<ProductPropertiesDO> getPropertiesPage(ProductPropertiesPageReqVO pageReqVO) {
        return productPropertiesMapper.selectPage(pageReqVO);
    }

}