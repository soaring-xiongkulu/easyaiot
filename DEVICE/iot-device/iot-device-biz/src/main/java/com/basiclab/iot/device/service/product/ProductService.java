package com.basiclab.iot.device.service.product;

import com.alibaba.fastjson2.JSONObject;
import com.basiclab.iot.common.domain.AjaxResult;
import com.basiclab.iot.device.domain.device.vo.Product;
import com.basiclab.iot.device.domain.product.model.ProductModel;
import com.basiclab.iot.device.domain.product.vo.param.ProductParamVO;
import com.basiclab.iot.device.domain.product.vo.result.ProductResultVO;
import org.springframework.web.multipart.MultipartFile;

import java.util.List;

/**
 * ProductService
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
public interface ProductService {


    int deleteByPrimaryKey(Long id);

    int insert(Product record);

    int insertOrUpdate(Product record);

    int insertOrUpdateSelective(Product record);

    int insertSelective(Product record);

    Product selectByPrimaryKey(Long id);

    int updateByPrimaryKeySelective(Product record);

    int updateByPrimaryKey(Product record);

    int updateBatch(List<Product> list);

    int updateBatchSelective(List<Product> list);

    int batchInsert(List<Product> list);

    /**
     * 产品模型导入
     *
     * @param file                   json文件
     * @param updateSupport          是否更新已经存在的产品模型数据
     * @param appId                  应用ID
     * @param templateIdentification 产品模型模板标识
     * @param status                 状态(字典值：启用  停用)
     * @return AjaxResult
     * @throws Exception
     */
    AjaxResult importProductJson(MultipartFile file, Boolean updateSupport, String appId, String templateIdentification, String status) throws Exception;


    /**
     * 解析产品模型数据
     *
     * @param content                产品模型数据
     * @param appId                  应用ID
     * @param templateIdentification 产品模型模板标识
     * @param status                 状态(字典值：启用  停用)
     * @return 解析结果
     * @throws Exception
     */
    public AjaxResult productJsonDataAnalysis(JSONObject content, String appId, String templateIdentification, String status) throws Exception;

    /**
     * 查询产品管理
     *
     * @param id 产品管理主键
     * @return 产品管理
     */
    public Product selectProductById(Long id);

    /**
     * 查询产品管理
     *
     * @param productIdentification 标识
     * @return 产品管理
     */
    public Product selectByProductIdentification(String productIdentification);

    /**
     * 查询产品管理 带服务、属性
     *
     * @param id 产品管理主键
     * @return 产品管理
     */
    public ProductModel selectFullProductById(Long id);

    /**
     * 查询产品管理列表
     *
     * @param product 产品管理
     * @return 产品管理集合
     */
    public List<Product> selectProductList(Product product);

    /**
     * 新增产品管理
     *
     * @param product 产品管理
     * @return 结果
     */
    public int insertProduct(Product product);

    /**
     * 修改产品管理
     *
     * @param product 产品管理
     * @return 结果
     */
    public int updateProduct(Product product);

    /**
     * 批量删除产品管理
     *
     * @param ids 需要删除的产品管理主键集合
     * @return 结果
     */
    public int deleteProductByIds(Long[] ids);

    /**
     * 删除产品管理信息
     *
     * @param id 产品管理主键
     * @return 结果
     */
    public int deleteProductById(Long id);


    Product findOneByProductName(String productName);


    List<Product> selectByManufacturerIdAndModelAndDeviceType(String manufacturerId, String model, String deviceType);


    Product findOneByManufacturerIdAndModelAndDeviceType(String manufacturerId, String model, String deviceType);


    List<Product> findAllByStatus(String status);


    Product findOneByManufacturerIdAndModelAndProtocolTypeAndStatus(String manufacturerId, String model, String protocolType, String status);


    Product findOneByIdAndStatus(Long id, String status);


    Product findOneByProductIdentificationAndProtocolType(String productIdentification);


    List<Product> findAllByIdInAndStatus(List<Long> ids, String status);

    List<Product> selectAllProductByStatus(String status);

    List<Product> selectProductByProductIdentificationList(List<String> productIdentificationList);

    /**
     * 根据产品标识查询产品详情
     *
     * @param productIdentification 产品标识
     * @return {@link ProductResultVO} 产品详情
     */
    ProductResultVO findOneByProductIdentification(String productIdentification);

    Long findProductTotal();

    List<Product> findProductsByPage(int offset, int pageSize);

    /**
     * 查询产品管理 带服务、属性、命令
     *
     * @param productIdentification 产品标识
     * @return 产品管理
     */
    ProductParamVO selectFullProductByProductIdentification(String productIdentification);

    /**
     * 产品赋能
     *
     * @param productIds 产品ID集合
     * @return 赋能结果
     */
    String productEmpowerment(Long[] productIds);
}

