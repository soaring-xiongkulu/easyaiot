package com.basiclab.iot.device.controller.product;

import com.basiclab.iot.common.adapter.ExcelUtil;
import com.basiclab.iot.common.domain.AjaxResult;
import com.basiclab.iot.common.domain.R;
import com.basiclab.iot.common.domain.TableDataInfo;
import com.basiclab.iot.common.utils.SecurityUtils;
import com.basiclab.iot.common.web.controller.BaseController;
import com.basiclab.iot.device.domain.device.vo.ProductProperties;
import com.basiclab.iot.device.service.product.ProductPropertiesService;
import org.springframework.web.bind.annotation.*;

import javax.annotation.Resource;
import javax.servlet.http.HttpServletResponse;
import java.io.IOException;
import java.util.List;

/**
 * (productProperties)表控制层
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@RestController
@RequestMapping("/productProperties")
public class ProductPropertiesController extends BaseController {
    /**
     * 服务对象
     */
    @Resource
    private ProductPropertiesService productPropertiesService;

    /**
     * 通过主键查询单条数据
     *
     * @param id 主键
     * @return 单条数据
     */
    @GetMapping("selectOne")
    public ProductProperties selectOne(Long id) {
        return productPropertiesService.selectByPrimaryKey(id);
    }

    /**
     * 通过主键查询单条数据
     *
     * @param id 主键
     * @return 单条数据
     */
    @GetMapping(value = "/selectByIdProperties/{id}")
    public R<?> selectByIdProperties(@PathVariable("id") Long id) {
        return R.ok(productPropertiesService.selectProductPropertiesById(id));
    }

    /**
     * 查询产品模型服务属性列表
     */
    //@PreAuthorize(hasPermi = "link:productProperties:list")
    @GetMapping("/list")
    public TableDataInfo list(ProductProperties productProperties) {
        startPage();
        List<ProductProperties> list = productPropertiesService.selectProductPropertiesList(productProperties);
        return getDataTable(list);
    }

    /**
     * 导出产品模型服务属性列表
     */
    //@PreAuthorize(hasPermi = "link:productProperties:export")
    //@Log(title = "产品模型服务属性", businessType = BusinessType.EXPORT)
    @PostMapping("/export")
    public void export(HttpServletResponse response, ProductProperties productProperties) throws IOException {
        List<ProductProperties> list = productPropertiesService.selectProductPropertiesList(productProperties);
        ExcelUtil<ProductProperties> util = new ExcelUtil<ProductProperties>(ProductProperties.class);
        util.exportExcel(response, list, "产品模型服务属性数据");
    }

    /**
     * 获取产品模型服务属性详细信息
     */
    //@PreAuthorize(hasPermi = "link:productProperties:query")
    @GetMapping(value = "/{id}")
    public AjaxResult getInfo(@PathVariable("id") Long id) {
        return AjaxResult.success(productPropertiesService.selectProductPropertiesById(id));
    }

    /**
     * 新增产品模型服务属性
     */
    //@PreAuthorize(hasPermi = "link:productProperties:add")
    //@Log(title = "产品模型服务属性", businessType = BusinessType.INSERT)
    @PostMapping
    public AjaxResult add(@RequestBody ProductProperties productProperties) {
        productProperties.setCreateBy(SecurityUtils.getUsername());
        return toAjax(productPropertiesService.insertProductProperties(productProperties));
    }

    /**
     * 修改产品模型服务属性
     */
    //@PreAuthorize(hasPermi = "link:productProperties:edit")
    //@Log(title = "产品模型服务属性", businessType = BusinessType.UPDATE)
    @PutMapping
    public AjaxResult edit(@RequestBody ProductProperties productProperties) {
        productProperties.setUpdateBy(SecurityUtils.getUsername());
        return toAjax(productPropertiesService.updateProductProperties(productProperties));
    }

    /**
     * 删除产品模型服务属性
     */
    //@PreAuthorize(hasPermi = "link:productProperties:remove")
    //@Log(title = "产品模型服务属性", businessType = BusinessType.DELETE)
    @DeleteMapping("/{ids}")
    public AjaxResult remove(@PathVariable Long[] ids) {
        return toAjax(productPropertiesService.deleteProductPropertiesByIds(ids));
    }

    @PostMapping("/selectPropertiesByPropertiesIdList")
    public R<?> selectPropertiesByPropertiesIdList(@RequestBody List<Long> propertiesIdList) {
        return R.ok(productPropertiesService.selectPropertiesByPropertiesIdList(propertiesIdList));
    }
}
