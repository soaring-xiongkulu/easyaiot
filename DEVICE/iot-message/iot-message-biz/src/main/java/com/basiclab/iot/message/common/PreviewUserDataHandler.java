package com.basiclab.iot.message.common;

import com.basiclab.iot.message.domain.entity.TPreviewUser;
import com.basiclab.iot.message.domain.model.vo.TPreviewUserExcelVo;
import com.basiclab.iot.message.mapper.TPreviewUserMapper;
import org.apache.commons.collections4.CollectionUtils;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Component;

import java.util.ArrayList;
import java.util.List;

/**
 * 目标用户数据处理
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 * @since 2024-07-17
 */
@Component
public class PreviewUserDataHandler {

    @Autowired
    private TPreviewUserMapper tPreviewUserMapper;

    public List<TPreviewUser> dataHandler(List<TPreviewUserExcelVo> previewUserExcelVos, List<String> errorList){
        List<TPreviewUser> tPreviewUsers = new ArrayList<>();
        if(CollectionUtils.isNotEmpty(previewUserExcelVos)){
            for(int i =0;i<previewUserExcelVos.size();i++){
                TPreviewUser tPreviewUser = new TPreviewUser();
                TPreviewUserExcelVo tPreviewUserExcelVo = previewUserExcelVos.get(i);
                String msgTypeName = tPreviewUserExcelVo.getMsgType();
                Integer msgType = getMsgType(msgTypeName);
                if(msgType == 0){
                    int errorLine = i+1;
                    errorList.add("第【"+errorLine+"】行消息类型输入错误，请在【阿里云短信、腾讯云短信、邮件、企业微信、http、钉钉】任选输入");
                }
                String previewUser = tPreviewUserExcelVo.getPreviewUser();
                int count = tPreviewUserMapper.getUserCount(msgType,previewUser);
                if(count > 0) {
                    int errorLine = i+1;
                    errorList.add("第【"+errorLine+"】行"+msgTypeName+","+previewUser+"已存在重复数据，请检查后重新导入");
                } else {
                    tPreviewUser.setMsgType(msgType);
                    tPreviewUser.setPreviewUser(previewUser);
                    tPreviewUsers.add(tPreviewUser);
                }
            }
        }
        return tPreviewUsers;
    }

    private static Integer getMsgType(String msgTypeName){
        switch (msgTypeName){
            case "阿里云短信" :
                return 1;
            case "腾讯云短信" :
                return 2;
            case "邮件" :
                return 3;
            case "企业微信" :
                return 4;
            case "http" :
                return 5;
            case "钉钉" :
                return 6;
            default: return 0;
        }
    }
}
