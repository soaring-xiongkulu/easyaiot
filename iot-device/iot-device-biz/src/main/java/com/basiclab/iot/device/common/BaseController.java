package com.basiclab.iot.device.common;

import com.github.pagehelper.PageHelper;
import com.github.pagehelper.PageInfo;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.web.bind.WebDataBinder;
import org.springframework.web.bind.annotation.InitBinder;

import java.beans.PropertyEditorSupport;
import java.util.Date;
import java.util.List;

/**
 * web层通用数据处理
 * 
 * @author basiclab
 */
public class BaseController
{
    protected final Logger logger = LoggerFactory.getLogger(this.getClass());

    /**
     * 将前台传递过来的日期格式的字符串，自动转化为Date类型
     */
    @InitBinder
    public void initBinder(WebDataBinder binder)
    {
        // Date 类型转换
        binder.registerCustomEditor(Date.class, new PropertyEditorSupport()
        {
            @Override
            public void setAsText(String text)
            {
                setValue(DateUtils.parseDate(text));
            }
        });
    }

    /**
     * 设置请求分页数据
     */
    protected void startPage()
    {
        PageDomain pageDomain = TableSupport.buildPageRequest();
        Integer pageNum = pageDomain.getPageNum();
        Integer pageSize = pageDomain.getPageSize();
        if (StringUtils.isNotNull(pageNum) && StringUtils.isNotNull(pageSize))
        {
            String orderBy = SqlUtil.escapeOrderBySql(pageDomain.getOrderBy());
            Boolean reasonable = pageDomain.getReasonable();
            PageHelper.startPage(pageNum, pageSize, orderBy).setReasonable(reasonable);
        }
    }

    /**
     * 响应请求分页数据
     */
    @SuppressWarnings({ "rawtypes", "unchecked" })
    protected TableDataInfo getDataTable(List<?> list)
    {
        TableDataInfo rspData = new TableDataInfo();
        rspData.setCode(HttpStatus.SUCCESS);
        rspData.setData(list);
        rspData.setMsg("查询成功");
        if(list == null || list.isEmpty()){
            rspData.setTotal(0);
        } else {
            rspData.setTotal(new PageInfo(list).getTotal());
        }
        return rspData;
    }

    /**
     * 响应返回结果
     * 
     * @param rows 影响行数
     * @return 操作结果
     */
    protected CommonResult toAjax(int rows)
    {
        return rows > 0 ? CommonResult.success() : CommonResult.error();
    }

    /**
     * 响应返回结果
     * 
     * @param result 结果
     * @return 操作结果
     */
    protected CommonResult toAjax(boolean result)
    {
        return result ? success() : error();
    }

    /**
     * 返回成功
     */
    public CommonResult success()
    {
        return CommonResult.success();
    }

    /**
     * 返回失败消息
     */
    public CommonResult error()
    {
        return CommonResult.error();
    }

    /**
     * 返回成功消息
     */
    public CommonResult success(String message)
    {
        return CommonResult.success(message);
    }

    /**
     * 返回成功消息
     */
    public CommonResult success(Object data)
    {
        return CommonResult.success(data);
    }

    /**
     * 返回成功消息
     */
    public CommonResult success(Long data)
    {
        return CommonResult.success(data);
    }

    /**
     * 返回失败消息
     */
    public CommonResult error(String message)
    {
        return CommonResult.error(message);
    }
}
