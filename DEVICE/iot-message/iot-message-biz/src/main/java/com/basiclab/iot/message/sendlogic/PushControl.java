package com.basiclab.iot.message.sendlogic;

import cn.hutool.log.Log;
import cn.hutool.log.LogFactory;
import com.basiclab.iot.message.mapper.TPushHistoryMapper;
import com.basiclab.iot.message.sendlogic.msgmaker.MsgMakerFactory;
import com.basiclab.iot.message.util.MybatisUtil;
import lombok.extern.slf4j.Slf4j;

/**
 * 推送控制
 */
@Slf4j
public class PushControl {
    private static final Log logger = LogFactory.get();
    /**
     * 是否空跑
     */
    public static boolean dryRun;

    public volatile static boolean saveResponseBody = false;

    private static TPushHistoryMapper pushHistoryMapper = MybatisUtil.getSqlSession().getMapper(TPushHistoryMapper.class);

    /**
     * 模板变量前缀
     */
    public static final String TEMPLATE_VAR_PREFIX = "var";


    /**
     * 推送前检查
     *
     * @return boolean
     */
//    public static boolean pushCheck() {
//        MainWindow mainWindow = MainWindow.getInstance();
//        PushForm pushForm = PushForm.getInstance();
//
//        if (StringUtils.isEmpty(MessageEditForm.getInstance().getMsgNameField().getText())) {
//            JOptionPane.showMessageDialog(mainWindow.getMainPanel(), "请先选择一条消息！", "提示",
//                    JOptionPane.INFORMATION_MESSAGE);
//            mainWindow.getTabbedPane().setSelectedIndex(2);
//
//            return false;
//        }
//        if (CollectionUtils.isEmpty(PushData.allUser)) {
//            int msgType = App.config.getMsgType();
//            String tipsTitle = "请先准备目标用户！";
//            if (msgType == MessageTypeEnum.HTTP_CODE) {
//                tipsTitle = "请先准备消息变量！";
//            }
//            JOptionPane.showMessageDialog(mainWindow.getMainPanel(), tipsTitle, "提示",
//                    JOptionPane.INFORMATION_MESSAGE);
//
//            return false;
//        }
//
//        return configCheck();
//    }

    /**
     * 配置检查
     *
     * @return isConfig
     */
//    public static boolean configCheck() {
//        SettingForm settingForm = SettingForm.getInstance();
//
//        int msgType = App.config.getMsgType();
//        switch (msgType) {
//            case MessageTypeEnum.MP_TEMPLATE_CODE:
//            case MessageTypeEnum.MP_SUBSCRIBE_CODE:
//            case MessageTypeEnum.KEFU_CODE:
//            case MessageTypeEnum.KEFU_PRIORITY_CODE:
//            case MessageTypeEnum.ALI_YUN_CODE:
//                String aliyunAccessKeyId = App.config.getAliyunAccessKeyId();
//                String aliyunAccessKeySecret = App.config.getAliyunAccessKeySecret();
//
//                if (StringUtils.isEmpty(aliyunAccessKeyId) || StringUtils.isEmpty(aliyunAccessKeySecret)) {
//                    JOptionPane.showMessageDialog(settingForm.getSettingPanel(),
//                            "请先在设置中填写并保存阿里云短信相关配置！", "提示",
//                            JOptionPane.INFORMATION_MESSAGE);
//                    return false;
//                }
//                break;
//            case MessageTypeEnum.TX_YUN_CODE:
//                String txyunAppId = App.config.getTxyunAppId();
//                String txyunAppKey = App.config.getTxyunAppKey();
//
//                if (StringUtils.isEmpty(txyunAppId) || StringUtils.isEmpty(txyunAppKey)) {
//                    JOptionPane.showMessageDialog(settingForm.getSettingPanel(),
//                            "请先在设置中填写并保存腾讯云短信相关配置！", "提示",
//                            JOptionPane.INFORMATION_MESSAGE);
//                    return false;
//                }
//                break;
//            case MessageTypeEnum.EMAIL_CODE:
//                String mailHost = App.config.getMailHost();
//                String mailFrom = App.config.getMailFrom();
//                if (StringUtils.isBlank(mailHost) || StringUtils.isBlank(mailFrom)) {
//                    JOptionPane.showMessageDialog(settingForm.getSettingPanel(),
//                            "请先在设置中填写并保存E-Mail相关配置！", "提示",
//                            JOptionPane.INFORMATION_MESSAGE);
//                    return false;
//                }
//                break;
//            case MessageTypeEnum.WX_CP_CODE:
//                String wxCpCorpId = App.config.getWxCpCorpId();
//                if (StringUtils.isBlank(wxCpCorpId)) {
//                    JOptionPane.showMessageDialog(settingForm.getSettingPanel(),
//                            "请先在设置中填写并保存企业微信相关配置！", "提示",
//                            JOptionPane.INFORMATION_MESSAGE);
//                    return false;
//                }
//                break;
//            default:
//        }
//        return true;
//    }

//    /**
//     * 推送停止或结束后保存数据
//     */
//    static void savePushData(int msgType,String msgName) throws IOException {
//        if (!PushData.toSendConcurrentLinkedQueue.isEmpty()) {
//            PushData.toSendList = new ArrayList<>(PushData.toSendConcurrentLinkedQueue);
//        }
//        File pushHisDir = new File(SystemUtil.CONFIG_HOME + "data" + File.separator + "push_his");
//        if (!pushHisDir.exists()) {
//            boolean mkdirs = pushHisDir.mkdirs();
//        }
//
//        String nowTime = DateUtil.now().replace(":", "_").replace(" ", "_");
//        CSVWriter writer;
//        List<File> fileList = new ArrayList<>();
//        // 保存已发送
//        if (PushData.sendSuccessList.size() > 0) {
//            File sendSuccessFile = new File(SystemUtil.CONFIG_HOME + "data" +
//                    File.separator + "push_his" + File.separator + MessageTypeEnum.getName(msgType) + "-" + msgName +
//                    "-发送成功-" + nowTime + ".csv");
//            FileUtil.touch(sendSuccessFile);
//            writer = new CSVWriter(new FileWriter(sendSuccessFile));
//
//            for (String[] str : PushData.sendSuccessList) {
//                writer.writeNext(str);
//            }
//            writer.close();
//
//            savePushResult(msgName, "发送成功", sendSuccessFile,msgType);
//            fileList.add(sendSuccessFile);
//            // 保存累计推送总数
////            App.config.setPushTotal(App.config.getPushTotal() + PushData.sendSuccessList.size());
////            App.config.save();
//        }
//
//        // 保存未发送
//        for (String[] str : PushData.sendSuccessList) {
//            if (msgType == MessageTypeEnum.HTTP_CODE && PushControl.saveResponseBody) {
//                str = ArrayUtils.remove(str, str.length - 1);
//                String[] finalStr = str;
//                PushData.toSendList = PushData.toSendList.stream().filter(strings -> !JSONUtil.toJsonStr(strings).equals(JSONUtil.toJsonStr(finalStr))).collect(Collectors.toList());
//            } else {
//                PushData.toSendList.remove(str);
//            }
//        }
//        for (String[] str : PushData.sendFailList) {
//            if (msgType == MessageTypeEnum.HTTP_CODE && PushControl.saveResponseBody) {
//                str = ArrayUtils.remove(str, str.length - 1);
//                String[] finalStr = str;
//                PushData.toSendList = PushData.toSendList.stream().filter(strings -> !JSONUtil.toJsonStr(strings).equals(JSONUtil.toJsonStr(finalStr))).collect(Collectors.toList());
//            } else {
//                PushData.toSendList.remove(str);
//            }
//        }
//
//        if (PushData.toSendList.size() > 0) {
//            File unSendFile = new File(SystemUtil.CONFIG_HOME + "data" + File.separator +
//                    "push_his" + File.separator + MessageTypeEnum.getName(msgType) + "-" + msgName + "-未发送-" + nowTime +
//                    ".csv");
//            FileUtil.touch(unSendFile);
//            writer = new CSVWriter(new FileWriter(unSendFile));
//            for (String[] str : PushData.toSendList) {
//                writer.writeNext(str);
//            }
//            writer.close();
//
//            savePushResult(msgName, "未发送", unSendFile,msgType);
//            fileList.add(unSendFile);
//        }
//
//        // 保存发送失败
//        if (PushData.sendFailList.size() > 0) {
//            File failSendFile = new File(SystemUtil.CONFIG_HOME + "data" + File.separator +
//                    "push_his" + File.separator + MessageTypeEnum.getName(msgType) + "-" + msgName + "-发送失败-" + nowTime + ".csv");
//            FileUtil.touch(failSendFile);
//            writer = new CSVWriter(new FileWriter(failSendFile));
//            for (String[] str : PushData.sendFailList) {
//                writer.writeNext(str);
//            }
//            writer.close();
//
//            savePushResult(msgName, "发送失败", failSendFile);
//            fileList.add(failSendFile);
//        }
//
//
//        // 发送推送结果邮件
//        if ((PushData.scheduling || PushData.fixRateScheduling)
//                && ScheduleForm.getInstance().getSendPushResultCheckBox().isSelected()) {
//            log.info("发送推送结果邮件开始");
//            String mailResultTo = ScheduleForm.getInstance().getMailResultToTextField().getText().replace("；", ";").replace(" ", "");
//            String[] mailTos = mailResultTo.split(";");
//            ArrayList<String> mailToList = new ArrayList<>(Arrays.asList(mailTos));
//
//            MailMsgSender mailMsgSender = new MailMsgSender();
//            String title = "WePush推送结果：【" + messageEditForm.getMsgNameField().getText()
//                    + "】" + PushData.sendSuccessList.size() + "成功；" + PushData.sendFailList.size() + "失败；"
//                    + PushData.toSendList.size() + "未发送";
//            StringBuilder contentBuilder = new StringBuilder();
//            contentBuilder.append("<h2>WePush推送结果</h2>");
//            contentBuilder.append("<p>消息类型：").append(MessageTypeEnum.getName(App.config.getMsgType())).append("</p>");
//            contentBuilder.append("<p>消息名称：").append(messageEditForm.getMsgNameField().getText()).append("</p>");
//            contentBuilder.append("<br/>");
//
//            contentBuilder.append("<p style='color:green'><strong>成功数：").append(PushData.sendSuccessList.size()).append("</strong></p>");
//            contentBuilder.append("<p style='color:red'><strong>失败数：").append(PushData.sendFailList.size()).append("</strong></p>");
//            contentBuilder.append("<p>未推送数：").append(PushData.toSendList.size()).append("</p>");
//            contentBuilder.append("<br/>");
//
//            contentBuilder.append("<p>开始时间：").append(DateFormatUtils.format(new Date(PushData.startTime), "yyyy-MM-dd HH:mm:ss")).append("</p>");
//            contentBuilder.append("<p>完毕时间：").append(DateFormatUtils.format(new Date(PushData.endTime), "yyyy-MM-dd HH:mm:ss")).append("</p>");
//            contentBuilder.append("<p>总耗时：").append(DateUtil.formatBetween(PushData.endTime - PushData.startTime, BetweenFormater.Level.SECOND)).append("</p>");
//            contentBuilder.append("<br/>");
//
//            contentBuilder.append("<p>详情请查看附件</p>");
//
//            contentBuilder.append("<br/>");
//            contentBuilder.append("<hr/>");
//            contentBuilder.append("<p>来自WePush，一款专注于批量推送的小而美的工具</p>");
//            contentBuilder.append("<img alt=\"WePush\" src=\"" + UiConsts.INTRODUCE_QRCODE_URL + "\">");
//
//            File[] files = new File[fileList.size()];
//            fileList.toArray(files);
//            mailMsgSender.sendPushResultMail(mailToList, title, contentBuilder.toString(), files);
//            logger.("发送推送结果邮件结束");
//        }
//    }

    /**
     * 准备消息构造器
     */
    static void prepareMsgMaker(int msgType) {
        MsgMakerFactory.getMsgMaker(msgType).prepare();

    }

    /**
     * 重新导入目标用户(定时任务)
     */
//    public static void reimportMembers() {
//        if (PushData.fixRateScheduling && ScheduleForm.getInstance().getReimportCheckBox().isSelected()) {
//            switch ((String) Objects.requireNonNull(ScheduleForm.getInstance().getReimportComboBox().getSelectedItem())) {
//                case "通过SQL导入":
//                    MemberListener.importFromSql();
//                    break;
//                case "通过文件导入":
//                    MemberListener.importFromFile();
//                    break;
//                case "导入所有关注公众号的用户":
//                    MemberListener.importWxAll();
//                    break;
//                case "导入选择的标签分组":
//                    long selectedTagId = MemberListener.userTagMap.get(MemberForm.getInstance().getMemberImportTagComboBox().getSelectedItem());
//                    try {
//                        MemberListener.getMpUserListByTag(selectedTagId);
//                    } catch (WxErroBaseException e) {
//                        logger.error(ExceptionUtils.getStackTrace(e));
//                    }
//                    MemberListener.renderMemberListTable();
//                    break;
//                case "导入选择的标签分组-取交集":
//                    selectedTagId = MemberListener.userTagMap.get(MemberForm.getInstance().getMemberImportTagComboBox().getSelectedItem());
//                    try {
//                        MemberListener.getMpUserListByTag(selectedTagId, true);
//                    } catch (WxErroBaseException e) {
//                        logger.error(ExceptionUtils.getStackTrace(e));
//                    }
//                    MemberListener.renderMemberListTable();
//                    break;
//                case "导入选择的标签分组-取并集":
//                    selectedTagId = MemberListener.userTagMap.get(MemberForm.getInstance().getMemberImportTagComboBox().getSelectedItem());
//                    try {
//                        MemberListener.getMpUserListByTag(selectedTagId, false);
//                    } catch (WxErroBaseException e) {
//                        logger.error(ExceptionUtils.getStackTrace(e));
//                    }
//                    MemberListener.renderMemberListTable();
//                    break;
//                case "导入企业通讯录中所有用户":
//                    MemberListener.importWxCpAll();
//                    break;
//                default:
//            }
//        }
//    }

}