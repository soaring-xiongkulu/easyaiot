package com.basiclab.iot.message.sendlogic.msgsender;

import cn.hutool.extra.mail.MailAccount;
import cn.hutool.extra.mail.MailUtil;
import com.alibaba.fastjson.JSONObject;
import com.basiclab.iot.message.domain.entity.MessageConfig;
import com.basiclab.iot.message.domain.entity.TMsgMail;
import com.basiclab.iot.message.domain.model.SendResult;
import com.basiclab.iot.message.mapper.TPreviewUserGroupMapper;
import com.basiclab.iot.message.mapper.TPreviewUserMapper;
import com.basiclab.iot.message.sendlogic.msgmaker.MailMsgMaker;
import com.basiclab.iot.message.service.MessageConfigService;
import lombok.extern.slf4j.Slf4j;
import org.apache.commons.collections.CollectionUtils;
import org.apache.commons.compress.utils.Lists;
import org.apache.commons.lang3.StringUtils;
import org.apache.commons.lang3.exception.ExceptionUtils;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

import java.io.*;
import java.net.HttpURLConnection;
import java.net.URL;
import java.net.URLConnection;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.Map;

/**
 * <pre>
 * E-Mail发送器
 * </pre>
 *
 * @author <a href="https://github.com/rememberber">RememBerBer</a>
 * @since 2019/6/23.
 */
@Slf4j
@Component
public class MailMsgSender {

    @Autowired
    private MailMsgMaker mailMsgMaker;

    @Autowired
    private MessageConfigService messageConfigService;

    @Value("${mail.annex.dir}")
    private String mailAnnexDir;

    @Autowired
    private TPreviewUserMapper tPreviewUserMapper;

    @Autowired
    private TPreviewUserGroupMapper tPreviewUserGroupMapper;

    public SendResult send(String msgId,String content) {
        log.info("邮件发送开始 params is:"+msgId);
        SendResult sendResult = new SendResult();

        try {
            TMsgMail mailMsg = mailMsgMaker.makeMsg(msgId,content);
            sendResult.setMsgName(mailMsg.getMsgName());
//            String previewUser = mailMsg.getPreviewUser();
            String files = mailMsg.getFiles();
            List<File> mailFiles = new ArrayList<>();
            getMailFiles(files, mailFiles);
            List<String> tos = Lists.newArrayList();
//            tos.add(previewUser);
            // 获取用户组中的目标用户
            String userGroupId = mailMsg.getUserGroupId();
            if(StringUtils.isNotEmpty(userGroupId)){
               String previewUserId = tPreviewUserGroupMapper.queryPreviewUserIds(userGroupId);
               List<String> previewUserIds = Arrays.asList(previewUserId.split(","));
               List<String> previewUsers = tPreviewUserMapper.queryPreviewUsers(previewUserIds);
               tos.addAll(previewUsers);
            }
            List<String> ccList = null;
            String cc = mailMsg.getCc();
            if (StringUtils.isNotBlank(cc)) {
                List<String> ccs = Arrays.asList(cc.split(","));
                ccList = new ArrayList<>(ccs);
            }
            MailAccount mailAccount = getMailAccount();
            if (CollectionUtils.isEmpty(mailFiles)) {
                MailUtil.send(mailAccount, tos, ccList, null, mailMsg.getTitle(), mailMsg.getContent(), true);
            } else {
                MailUtil.send(mailAccount, tos, ccList, null, mailMsg.getTitle(), mailMsg.getContent(), true, mailFiles.toArray(new File[0]));
            }
            sendResult.setSuccess(true);

        } catch (Exception e) {
            sendResult.setSuccess(false);
            sendResult.setInfo(e.getMessage());
            log.error(ExceptionUtils.getStackTrace(e));
        }

        return sendResult;
    }

    private void getMailFiles(String files, List<File> mailFiles) throws IOException {
        if(StringUtils.isNotEmpty(files)) {
            JSONObject jsonObject = JSONObject.parseObject(files);
            URL url = new URL(jsonObject.getString("filePath"));
            if(url != null) {
                URLConnection urlConnection = url.openConnection();
                HttpURLConnection httpURLConnection = (HttpURLConnection) urlConnection;// http的连接类
                httpURLConnection.setConnectTimeout(1000 * 5);//设置超时
                httpURLConnection.setRequestMethod("GET");//设置请求方式，默认是GET
                httpURLConnection.setRequestProperty("Charset", "UTF-8");// 设置字符编码
                httpURLConnection.connect();// 打开连接
                BufferedInputStream bin = new BufferedInputStream(httpURLConnection.getInputStream());
                String path = mailAnnexDir + File.separatorChar + jsonObject.getString("fileName");// 指定存放位置
                log.info("存储位置目录：   {}", path);
                File file = new File(path);
                mailFiles.add(file);
                // 校验文件夹目录是否存在，不存在就创建一个目录
                if (!file.getParentFile().exists()) {
                    file.getParentFile().mkdirs();
                }
                OutputStream out = new FileOutputStream(file);
                int size = 0;
                byte[] b = new byte[20480];
                //把输入流的文件读取到字节数据b中，然后输出到指定目录的文件
                while ((size = bin.read(b)) != -1) {
                    out.write(b, 0, size);
                }
                // 关闭资源
                bin.close();
                out.close();
            }
        }
    }


    public SendResult sendTestMail(String tos) {
        SendResult sendResult = new SendResult();

        try {
            MailAccount mailAccount = getMailAccount();
            MailUtil.send(mailAccount, tos, "这是一封来自统一消息通知平台的测试邮件",
                    "<h1>恭喜，配置正确，邮件发送成功！</h1><p>来自统一消息通知平台，一款专注于批量推送的小而美的工具。</p>", true);
            sendResult.setSuccess(true);
        } catch (Exception e) {
            sendResult.setSuccess(false);
            sendResult.setInfo(e.getMessage());
            log.error(e.toString());
        }

        return sendResult;
    }

    /**
     * 发送推送结果
     *
     * @param tos
     * @return
     */
    public SendResult sendPushResultMail(List<String> tos, String title, String content, File[] files) {
        SendResult sendResult = new SendResult();

        try {
            MailAccount mailAccount = getMailAccount();
            MailUtil.send(mailAccount, tos, title, content, true, files);
            sendResult.setSuccess(true);
        } catch (Exception e) {
            sendResult.setSuccess(false);
            sendResult.setInfo(e.getMessage());
            log.error(e.toString());
        }

        return sendResult;
    }

    /**
     * 获取E-Mail发送客户端
     *
     * @return MailAccount
     */
    private MailAccount getMailAccount() {
        MailAccount mailAccount = null;
        if (mailAccount == null) {
            synchronized (MailMsgSender.class) {
                if (mailAccount == null) {
                    MessageConfig messageConfig = messageConfigService.queryByMsgType(3);
                    Map<String,Object> emailConfig = messageConfig.getConfigurationMap();
                    String mailHost = (String) emailConfig.get("mailHost");
                    Integer mailPort = (Integer) emailConfig.get("mailPort");
                    String mailFrom = (String) emailConfig.get("mailFrom");
                    String mailUser = (String) emailConfig.get("mailUser");
                    String mailPassword = (String) emailConfig.get("mailPassword");

                    mailAccount = new MailAccount();
                    mailAccount.setHost(mailHost);
                    mailAccount.setPort(Integer.valueOf(mailPort));
                    mailAccount.setAuth(true);
                    mailAccount.setFrom(mailFrom);
                    mailAccount.setUser(mailUser);
                    mailAccount.setPass(mailPassword);
                    mailAccount.setSslEnable((Boolean) emailConfig.get("sslEnable"));
                    mailAccount.setStarttlsEnable((Boolean) emailConfig.get("starttlsEnable"));
                }
            }
        }
        return mailAccount;
    }
}
