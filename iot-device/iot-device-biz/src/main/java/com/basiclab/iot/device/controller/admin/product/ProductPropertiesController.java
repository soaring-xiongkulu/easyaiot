package com.basiclab.iot.device.controller.admin.product;

import com.basiclab.iot.device.common.CommonResult;
import com.basiclab.iot.device.common.R;
import com.basiclab.iot.device.common.SecurityUtils;
import com.basiclab.iot.device.common.TableDataInfo;
import com.basiclab.iot.device.service.product_properties.ProductPropertiesService;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.*;

import javax.annotation.Resource;
import java.util.List;

/**
 * (productProperties)表控制层
 *
 * @author basiclab
 */
@RestController
@RequestMapping("/productProperties")
public class ProductPropertiesController extends com.basiclab.iot.device.common.BaseController {
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
    @PreAuthorize("@ss.hasPermission('link:productProperties:list')")
    @GetMapping("/list")
    public TableDataInfo list(ProductProperties productProperties) {
        startPage();
        List<ProductProperties> list = productPropertiesService.selectProductPropertiesList(productProperties);
        return getDataTable(list);
    }

    /**
     * 获取产品模型服务属性详细信息
     */
    @PreAuthorize("@ss.hasPermission('link:productProperties:query')")
    @GetMapping(value = "/{id}")
    public CommonResult getInfo(@PathVariable("id") Long id) {
        return CommonResult.success(productPropertiesService.selectProductPropertiesById(id));
    }

    /**
     * 新增产品模型服务属性
     */
    @PreAuthorize("@ss.hasPermission('link:productProperties:add')")
    @PostMapping
    public CommonResult add(@RequestBody ProductProperties productProperties) {
        productProperties.setCreateBy(SecurityUtils.getUsername());
        return toAjax(productPropertiesService.insertProductProperties(productProperties));
    }
}
