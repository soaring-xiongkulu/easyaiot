package com.basiclab.iot.common.domain;

import io.swagger.annotations.ApiModel;
import io.swagger.annotations.ApiModelProperty;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.io.Serializable;
import java.util.ArrayList;
import java.util.List;

/**
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 * @desc
 * @created 2025-05-27
 */
@Data
@NoArgsConstructor
@ApiModel(value = "分页查询参数", description = "用于指定分页查询相关参数")
public class PageQo implements Serializable {

    @ApiModelProperty(value = "当前页", example = "1")
    protected int pageNo = 1;

    @ApiModelProperty(value = "每页显示大小", example = "10")
    protected int pageSize = 10;

    @ApiModelProperty(value = "排序字段列表")
    protected List<SortOrder> sortOrders = new ArrayList<>();

    public void addSortOrder(String property, Direction direction) {
        this.sortOrders.add(new SortOrder(property, direction));
    }

    public void addSortOrder(String property, String direction) {
        this.sortOrders.add(new SortOrder(property, Direction.fromStringOrNull(direction)));
    }

    public PageQo(int pageNo, int pageSize) {
        this.pageNo = pageNo;
        this.pageSize = pageSize;
    }
}
