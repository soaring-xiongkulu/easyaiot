package com.basiclab.iot.message.sendlogic.msgmaker;

import com.basiclab.iot.message.domain.entity.TMsgSms;
import com.basiclab.iot.message.domain.entity.TTemplateData;
import com.basiclab.iot.message.mapper.TMsgSmsMapper;
import org.apache.commons.compress.utils.Lists;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Component;

import javax.swing.table.DefaultTableModel;
import java.util.List;

/**
 * 腾讯云模板-短信加工器
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 * @since 2024-07-18
 */
@Component
public class TxYunMsgMaker extends BaseMsgMaker implements IMsgMaker{

    public static int templateId;

    public static List<String> paramList;

    @Autowired
    private TMsgSmsMapper tMsgSmsMapper;

    /**
     * 准备(界面字段等)
     */
    @Override
    public void prepare() {
        templateId = 0;


        //DefaultTableModel tableModel = (DefaultTableModel) TxYunMsgForm.getInstance().getTemplateMsgDataTable().getModel();
        DefaultTableModel tableModel = new DefaultTableModel();
        int rowCount = tableModel.getRowCount();
        paramList = Lists.newArrayList();
        for (int i = 0; i < rowCount; i++) {
            String value = ((String) tableModel.getValueAt(i, 1));
            paramList.add(value);
        }
    }

    /**
     * 组织腾讯云短信消息
     *
     * @param msgId 消息信息
     * @return String[]
     */
    @Override
    public String[] makeMsg(String msgId) {

        TMsgSms tMsgSms = tMsgSmsMapper.selectByPrimaryKey(msgId);
        List<TTemplateData> templateDataList = tMsgSms.getTemplateDataList();
        for (int i = 0; i < templateDataList.size(); i++) {
            paramList.set(i, templateDataList.get(i).getValue());
        }
        String[] paramArray = new String[paramList.size()];
        return paramList.toArray(paramArray);
    }
}
