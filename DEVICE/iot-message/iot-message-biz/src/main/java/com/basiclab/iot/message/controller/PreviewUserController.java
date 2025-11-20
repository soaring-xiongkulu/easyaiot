package com.basiclab.iot.message.controller;

import com.alibaba.fastjson.JSONObject;
import com.basiclab.iot.common.web.controller.BaseController;
import com.basiclab.iot.common.domain.AjaxResult;
import com.basiclab.iot.common.domain.TableDataInfo;
import com.basiclab.iot.message.domain.entity.TPreviewUser;
import com.basiclab.iot.message.domain.model.vo.TPreviewUserExcelVo;
import com.basiclab.iot.message.common.PreviewUserDataHandler;
import com.basiclab.iot.message.service.TPreviewUserService;
import com.basiclab.iot.message.util.ExcelUtils;
import io.swagger.v3.oas.annotations.tags.Tag;
import io.swagger.annotations.ApiOperation;
import org.apache.commons.collections4.CollectionUtils;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

import javax.servlet.http.HttpServletResponse;
import java.io.IOException;
import java.util.ArrayList;
import java.util.List;

@RestController
@RequestMapping("/message/preview/user")
@Tag(name  ="预先用户管理")
public class PreviewUserController extends BaseController {

    @Autowired
    private TPreviewUserService tPreviewUserService;

    @Autowired
    private PreviewUserDataHandler dataHandler;

    @PostMapping("/add")
    @ApiOperation("新增")
    public AjaxResult add(@RequestBody TPreviewUser tPreviewUser){
        return tPreviewUserService.add(tPreviewUser);
    }
    @PostMapping("/update")
    @ApiOperation("更新")
    public AjaxResult update(@RequestBody TPreviewUser tPreviewUser){
        return AjaxResult.success(tPreviewUserService.update(tPreviewUser));
    }

    @GetMapping("/delete")
    @ApiOperation("删除")
    public AjaxResult delete(String id){
        return AjaxResult.success(tPreviewUserService.delete(id));
    }

    @GetMapping("/query")
    @ApiOperation("查询")
    public TableDataInfo query(@ModelAttribute TPreviewUser tPreviewUser){
        startPage();
        List<TPreviewUser> list = tPreviewUserService.query(tPreviewUser);
        return getDataTable(list);
    }

    @GetMapping("/queryByMsgType")
    @ApiOperation("通过消息类型查询")
    public AjaxResult queryByMsgType(int msgType){
        return AjaxResult.success(tPreviewUserService.queryByMsgType(msgType));

    }

    @GetMapping("/exportExcel")
    @ApiOperation("导入excel")
    public void exportExcel(HttpServletResponse response) throws IOException {
        List<TPreviewUserExcelVo> tPreviewUsers = new ArrayList<>();
        ExcelUtils.write(response,"目标用户导入模板","数据", TPreviewUserExcelVo.class,tPreviewUsers);
    }

    @PostMapping("/import")
    @ApiOperation("导入")
    public AjaxResult importUser(@RequestPart("file") MultipartFile file) throws IOException {
        List<TPreviewUserExcelVo> tPreviewUsers = ExcelUtils.read(file, TPreviewUserExcelVo.class);
        List<String> errorList = new ArrayList<>();
        List<TPreviewUser> tPreviewUserList = dataHandler.dataHandler(tPreviewUsers,errorList);
        if(CollectionUtils.isNotEmpty(errorList)){
            return AjaxResult.error(500, JSONObject.toJSONString(errorList));
        }
        for (TPreviewUser tPreviewUser : CollectionUtils.emptyIfNull(tPreviewUserList)){
            tPreviewUserService.add(tPreviewUser);
        }
        return AjaxResult.success("导入成功");
    }

}
