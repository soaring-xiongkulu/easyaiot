package com.basiclab.iot.device.controller.product;

import com.basiclab.iot.common.domain.AjaxResult;
import com.basiclab.iot.common.domain.R;
import com.basiclab.iot.common.domain.TableDataInfo;
import com.basiclab.iot.common.utils.SecurityUtils;
import com.basiclab.iot.common.web.controller.BaseController;
import com.basiclab.iot.device.domain.device.vo.ProductEvent;
import com.basiclab.iot.device.service.product.ProductEventService;
import io.swagger.annotations.Api;
import io.swagger.annotations.ApiOperation;
import org.springframework.web.bind.annotation.*;

import javax.annotation.Resource;
import java.util.List;

/**
 * ProductEventController
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */

@Api(tags = "产品事件管理")
@RestController
@RequestMapping("/productEvent")
public class ProductEventController extends BaseController {

    @Resource
    private ProductEventService productEventService;

    /**
     * 查询产品事件列表
     */
    @ApiOperation("查询产品事件列表")
    @GetMapping("/list")
    public TableDataInfo list(ProductEvent productEvent) {
        startPage();
        List<ProductEvent> list = productEventService.selectList(productEvent);
        return getDataTable(list);
    }

    /**
     * 获取产品事件详细信息
     */
    @ApiOperation("获取产品事件详细信息")
    @GetMapping(value = "/{id}")
    public AjaxResult getInfo(@PathVariable("id") Long id) {
        return AjaxResult.success(productEventService.queryById(id));
    }

    /**
     * 新增产品事件
     */
    @ApiOperation("新增产品事件")
    @PostMapping
    public AjaxResult add(@RequestBody ProductEvent productEvent) {
        productEvent.setCreateBy(SecurityUtils.getUsername());
        return toAjax(productEventService.insert(productEvent));
    }

    /**
     * 修改产品事件
     */
    @ApiOperation("修改产品事件")
    @PutMapping
    public AjaxResult edit(@RequestBody ProductEvent productEvent) {
        productEvent.setUpdateBy(SecurityUtils.getUsername());
        return toAjax(productEventService.update(productEvent));
    }

    /**
     * 删除产品事件
     */
    @ApiOperation("删除产品事件")
    @DeleteMapping("/{ids}")
    public AjaxResult remove(@PathVariable Long[] ids) {
        return toAjax(productEventService.deleteByIds(ids));
    }
}

