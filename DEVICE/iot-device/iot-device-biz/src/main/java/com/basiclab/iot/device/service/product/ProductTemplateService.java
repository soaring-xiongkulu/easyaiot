package com.basiclab.iot.device.service.product;

import com.basiclab.iot.device.domain.device.vo.ProductTemplate;
import com.basiclab.iot.device.domain.product.model.ProductTemplateModel;

import java.util.List;

/**
 * @author: EasyAIoT
 * @email: andywebjava@163.com
 */
public interface ProductTemplateService {


    int deleteByPrimaryKey(Long id);

    int insert(ProductTemplate record);

    int insertOrUpdate(ProductTemplate record);

    int insertOrUpdateSelective(ProductTemplate record);

    int insertSelective(ProductTemplate record);

    ProductTemplate selectByPrimaryKey(Long id);

    int updateByPrimaryKeySelective(ProductTemplate record);

    int updateByPrimaryKey(ProductTemplate record);

    int updateBatch(List<ProductTemplate> list);

    int updateBatchSelective(List<ProductTemplate> list);

    int batchInsert(List<ProductTemplate> list);

    /**
     * 查询产品模板
     *
     * @param id 产品模板主键
     * @return 产品模板
     */
    public ProductTemplate selectProductTemplateById(Long id);

    /**
     * 查询产品模板 带服务、属性
     *
     * @param id 产品模板主键
     * @return 产品模板
     */
    ProductTemplateModel selectFullProductTemplateById(Long id);

    /**
     * 查询产品模板列表
     *
     * @param productTemplate 产品模板
     * @return 产品模板集合
     */
    public List<ProductTemplate> selectProductTemplateList(ProductTemplate productTemplate);

    /**
     * 新增产品模板
     *
     * @param productTemplate 产品模板
     * @return 结果
     */
    public int insertProductTemplate(ProductTemplate productTemplate);

    /**
     * 修改产品模板
     *
     * @param productTemplate 产品模板
     * @return 结果
     */
    public int updateProductTemplate(ProductTemplate productTemplate);

    /**
     * 批量删除产品模板
     *
     * @param ids 需要删除的产品模板主键集合
     * @return 结果
     */
    public int deleteProductTemplateByIds(Long[] ids);
}



