package com.basiclab.iot.device.controller.product;

import com.basiclab.iot.common.domain.AjaxResult;
import com.basiclab.iot.common.domain.R;
import com.basiclab.iot.common.domain.TableDataInfo;
import com.basiclab.iot.common.utils.SecurityUtils;
import com.basiclab.iot.common.web.controller.BaseController;
import com.basiclab.iot.device.domain.device.vo.ProductEventResponse;
import com.basiclab.iot.device.service.product.ProductEventResponseService;
import io.swagger.annotations.Api;
import io.swagger.annotations.ApiOperation;
import org.springframework.web.bind.annotation.*;

import javax.annotation.Resource;
import java.util.List;

/**
 * ProductEventResponseController
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */

@Api(tags = "产品事件响应管理")
@RestController
@RequestMapping("/productEventResponse")
public class ProductEventResponseController extends BaseController {

    @Resource
    private ProductEventResponseService productEventResponseService;

    /**
     * 查询产品事件响应列表
     */
    @ApiOperation("查询产品事件响应列表")
    @GetMapping("/list")
    public TableDataInfo list(ProductEventResponse productEventResponse) {
        startPage();
        List<ProductEventResponse> list = productEventResponseService.selectList(productEventResponse);
        return getDataTable(list);
    }

    /**
     * 获取产品事件响应详细信息
     */
    @ApiOperation("获取产品事件响应详细信息")
    @GetMapping(value = "/{id}")
    public AjaxResult getInfo(@PathVariable("id") Long id) {
        return AjaxResult.success(productEventResponseService.queryById(id));
    }

    /**
     * 新增产品事件响应
     */
    @ApiOperation("新增产品事件响应")
    @PostMapping
    public AjaxResult add(@RequestBody ProductEventResponse productEventResponse) {
        productEventResponse.setCreateBy(SecurityUtils.getUsername());
        return toAjax(productEventResponseService.insert(productEventResponse));
    }

    /**
     * 修改产品事件响应
     */
    @ApiOperation("修改产品事件响应")
    @PutMapping
    public AjaxResult edit(@RequestBody ProductEventResponse productEventResponse) {
        productEventResponse.setUpdateBy(SecurityUtils.getUsername());
        return toAjax(productEventResponseService.update(productEventResponse));
    }

    /**
     * 删除产品事件响应
     */
    @ApiOperation("删除产品事件响应")
    @DeleteMapping("/{ids}")
    public AjaxResult remove(@PathVariable Long[] ids) {
        return toAjax(productEventResponseService.deleteByIds(ids));
    }
}

