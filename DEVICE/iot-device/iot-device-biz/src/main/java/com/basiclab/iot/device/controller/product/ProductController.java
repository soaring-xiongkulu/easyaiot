package com.basiclab.iot.device.controller.product;

import com.alibaba.fastjson2.JSONObject;
import com.basiclab.iot.common.adapter.ExcelUtil;
import com.basiclab.iot.common.annotation.NoRepeatSubmit;
import com.basiclab.iot.common.domain.AjaxResult;
import com.basiclab.iot.common.domain.R;
import com.basiclab.iot.common.domain.TableDataInfo;
import com.basiclab.iot.common.service.RedisService;
import com.basiclab.iot.common.utils.StringUtils;
import com.basiclab.iot.common.web.controller.BaseController;
import com.basiclab.iot.device.domain.device.vo.CommandWrapperParamReq;
import com.basiclab.iot.device.domain.device.vo.Product;
import com.basiclab.iot.device.domain.product.model.ProductModel;
import com.basiclab.iot.device.service.product.ProductService;
import com.basiclab.iot.file.RemoteFileService;
import io.swagger.annotations.ApiImplicitParam;
import io.swagger.annotations.ApiImplicitParams;
import io.swagger.annotations.ApiOperation;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

import javax.annotation.Resource;
import javax.servlet.http.HttpServletResponse;
import javax.validation.Valid;
import java.io.IOException;
import java.util.List;
import java.util.Map;

/**
 * ProductController
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */

@Tag(name = "产品管理")
@RestController
@RequestMapping("/product")
@Slf4j
public class ProductController extends BaseController {
    /**
     * 服务对象
     */
    @Resource
    private ProductService productService;
    @Resource
    private RemoteFileService remoteFileService;
    @Autowired
    private RedisService redisService;

    /**
     * 通过主键查询单条数据
     *
     * @param id 主键
     * @return 单条数据
     */
    @GetMapping("/selectOne")
    public Product selectOne(Long id) {
        return productService.selectByPrimaryKey(id);
    }

    /**
     * 通过主产品标识查询产品
     *
     * @param productIdentification 产品标识
     * @return 单条数据
     */
    @GetMapping("/selectByProductIdentification/{productIdentification}")
    public R<?> selectByProductIdentification(@PathVariable(value = "productIdentification") String productIdentification) {
        return R.ok(productService.selectByProductIdentification(productIdentification));
    }

    /**
     * 导入产品模型json数据
     *
     * @param file                   json文件
     * @param updateSupport          是否更新已经存在的产品模型数据
     * @param appId                  应用ID
     * @param templateIdentification 产品模型模板标识
     * @param status                 状态(字典值：启用  停用)
     * @return AjaxResult
     * @throws Exception
     */
    // @PreAuthorize("@ss.hasPermission('link:product:import')")
    ////@Log(title = "产品管理", businessType = BusinessType.IMPORT)
    @PostMapping("/importProductJsonFile")
    public AjaxResult importProductJson(MultipartFile file,
                                        Boolean updateSupport,
                                        String appId,
                                        String templateIdentification,
                                        String status
    ) throws Exception {
        AjaxResult ajaxResult = productService.importProductJson(file, updateSupport, appId, templateIdentification, status);
        //存储产品模型原始文件
//        final R<SysFile> uploadMessage = remoteFileService.upload(file);
        return ajaxResult;
    }

    /**
     * 查询产品管理列表
     */
    @ApiOperation("查询产品列表")
    @ApiImplicitParams({
            @ApiImplicitParam(name = "pageNum", value = "页码", dataType = "int", dataTypeClass = Integer.class, paramType = "query", example = "1", required = true),
            @ApiImplicitParam(name = "pageSize", value = "每页显示记录数", dataType = "int", dataTypeClass = Integer.class, paramType = "query", example = "10", required = true),
            @ApiImplicitParam(name = "orderByColumn", value = "排序字段", dataType = "string", dataTypeClass = String.class, paramType = "query"),
            @ApiImplicitParam(name = "isAsc", value = "排序方式（asc/desc）", dataType = "string", dataTypeClass = String.class, paramType = "query")
    })
    // @PreAuthorize("@ss.hasPermission('link:product:list')")
    @GetMapping("/list")
    public TableDataInfo list(Product product) {
        startPage();
        List<Product> list = productService.selectProductList(product);
        return getDataTable(list);
    }

    /**
     * 导出产品管理列表
     */
    // @PreAuthorize("@ss.hasPermission('link:product:export')")
    ////@Log(title = "产品管理", businessType = BusinessType.EXPORT)
    @PostMapping("/export")
    public void export(HttpServletResponse response, Product product) throws IOException {
        List<Product> list = productService.selectProductList(product);
        ExcelUtil<Product> util = new ExcelUtil<Product>(Product.class);
        util.exportExcel(response, list, "产品管理数据");
    }

    /**
     * 获取产品管理详细信息
     */
    @ApiOperation("获取产品详细信息")
    // @PreAuthorize("@ss.hasPermission('link:product:query')")
    @GetMapping(value = "/{id}")
    public AjaxResult getInfo(@PathVariable("id") Long id) {
        return AjaxResult.success(productService.selectProductById(id));
    }

    /**
     * 获取产品管理详细信息
     */
    // @PreAuthorize("@ss.hasPermission('link:product:query')")
    @GetMapping(value = "/getFullInfo/{id}")
    public AjaxResult getFullInfo(@PathVariable("id") Long id) {
        ProductModel productModel = productService.selectFullProductById(id);
        return AjaxResult.success(productModel);
    }

    /**
     * 新增产品管理
     */
    @ApiOperation("添加产品")
    @NoRepeatSubmit
    // @PreAuthorize("@ss.hasPermission('link:product:add')")
    ////@Log(title = "产品管理", businessType = BusinessType.INSERT)
    @PostMapping
    public AjaxResult add(@RequestBody Product product) {

        int row = productService.insertProduct(product);

        if (row == -1) {
            return AjaxResult.error("产品名称已经存在！");
        }

        return toAjax(row);
    }

    /**
     * 修改产品管理
     */
    @ApiOperation("编辑产品")
    @NoRepeatSubmit
    // @PreAuthorize("@ss.hasPermission('link:product:edit')")
    ////@Log(title = "产品管理", businessType = BusinessType.UPDATE)
    @PutMapping
    public AjaxResult edit(@RequestBody Product product) {
        return toAjax(productService.updateProduct(product));
    }

    /**
     * 删除产品管理
     */
    @ApiOperation("删除产品")
    // @PreAuthorize("@ss.hasPermission('link:product:remove')")
    ////@Log(title = "产品管理", businessType = BusinessType.DELETE)
    @DeleteMapping("/{ids}")
    public AjaxResult remove(@PathVariable Long[] ids) {
        return toAjax(productService.deleteProductByIds(ids));
    }


    /**
     * 校验产品名称是否存在
     *
     * @param productName
     * @return
     */
    @GetMapping(value = "/validationFindOneByProductName/{productName}")
    public AjaxResult validationFindOneByProductName(@PathVariable("productName") String productName) {
        Product oneByProductName = productService.findOneByProductName(productName);
        if (StringUtils.isNull(oneByProductName)) {
            AjaxResult.success("产品名称可用");
        }
        return AjaxResult.error("产品名称已存在");
    }

    /**
     * 快捷生成产品模型json数据
     *
     * @param params (content 模型json数据、appId 应用ID、templateIdentification  产品模型模板标识、status 状态(字典值：启用  停用))
     * @return AjaxResult
     * @throws Exception
     */
    @NoRepeatSubmit
    // @PreAuthorize("@ss.hasPermission('link:product:generate')")
    ////@Log(title = "产品管理", businessType = BusinessType.INSERT)
    @PostMapping("/generateProductJson")
    public AjaxResult generateProductJson(@RequestBody Map<String, Object> params) throws Exception {
        final Object content = params.get("content");
        final Object appId = params.get("appId");
        final Object templateIdentification = params.get("templateIdentification");
        final Object status = params.get("status");
        AjaxResult ajaxResult = productService.productJsonDataAnalysis(JSONObject.parseObject(content.toString()), appId.toString(), templateIdentification.toString(), status.toString());
        return ajaxResult;
    }


    /**
     * 获取所有产品
     *
     * @param status 状态
     * @return 列表数据
     */
    @GetMapping("/selectAllProduct/{status}")
    public R<?> selectAllProductByStatus(@PathVariable(value = "status") String status) {
        return R.ok(productService.selectAllProductByStatus(status));
    }

    @PostMapping("/selectProductByProductIdentificationList")
    public R<?> selectProductByProductIdentificationList(@RequestBody List<String> productIdentificationList) {
        return R.ok(productService.selectProductByProductIdentificationList(productIdentificationList));
    }


//    // @PreAuthorize("@ss.hasPermission('link:product:empowerment')")
//    @ApiOperation(value = "产品赋能", httpMethod = "GET", notes = "产品赋能")

    /// /@Log(title = "产品管理", businessType = BusinessType.OTHER)
    @GetMapping(value = "/productEmpowerment/{productIds}")
    public AjaxResult productEmpowerment(@PathVariable("productIds") Long[] productIds) {
        try {
            return AjaxResult.success(productService.productEmpowerment(productIds));
        } catch (Exception e) {
            log.error(e.getMessage());
        }
        return AjaxResult.error("产品赋能异常,请联系管理员");
    }
}
