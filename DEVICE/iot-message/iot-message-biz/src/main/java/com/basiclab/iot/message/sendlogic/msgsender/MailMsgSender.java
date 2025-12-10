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
            String previewUser = mailMsg.getPreviewUser();
            String files = mailMsg.getFiles();
            List<File> mailFiles = new ArrayList<>();
            getMailFiles(files, mailFiles);
            List<String> tos = Lists.newArrayList();
            
            // 优先使用直接指定的收件人（previewUser）
            if (StringUtils.isNotEmpty(previewUser)) {
                // 支持多个收件人，用逗号分隔
                String[] recipients = previewUser.split(",");
                for (String recipient : recipients) {
                    String trimmedRecipient = recipient.trim();
                    if (StringUtils.isNotEmpty(trimmedRecipient)) {
                        tos.add(trimmedRecipient);
                    }
                }
                log.info("从previewUser获取收件人: {}", tos);
            }
            
            // 如果previewUser为空，则从用户组中获取目标用户
            String userGroupId = mailMsg.getUserGroupId();
            log.info("邮件模板 userGroupId: {}", userGroupId);
            if (CollectionUtils.isEmpty(tos) && StringUtils.isNotEmpty(userGroupId)) {
               String previewUserId = tPreviewUserGroupMapper.queryPreviewUserIds(userGroupId);
               log.info("查询到的 previewUserId: {}", previewUserId);
               if(StringUtils.isNotEmpty(previewUserId)){
                   List<String> previewUserIds = Arrays.asList(previewUserId.split(","));
                   List<String> previewUsers = tPreviewUserMapper.queryPreviewUsers(previewUserIds);
                   log.info("查询到的收件人列表: {}", previewUsers);
                   tos.addAll(previewUsers);
               } else {
                   log.warn("用户组 {} 中没有配置用户ID", userGroupId);
               }
            } else if (CollectionUtils.isEmpty(tos)) {
                log.warn("邮件模板中没有配置 userGroupId 且 previewUser 为空");
            }
            
            // 验证收件人列表是否为空
            if (CollectionUtils.isEmpty(tos)) {
                String errorMsg = "收件人列表为空，无法发送邮件。请检查邮件模板是否配置了收件人(previewUser)或用户组(userGroupId)，以及用户组中是否包含有效的邮箱地址";
                log.error(errorMsg);
                sendResult.setSuccess(false);
                sendResult.setInfo(errorMsg);
                return sendResult;
            }
            
            log.info("邮件收件人列表: {}, 抄送列表: {}", tos, mailMsg.getCc());
            
            List<String> ccList = null;
            String cc = mailMsg.getCc();
            if (StringUtils.isNotBlank(cc)) {
                List<String> ccs = Arrays.asList(cc.split(","));
                ccList = new ArrayList<>(ccs);
            }
            MailAccount mailAccount = getMailAccount();
            log.info("开始发送邮件，标题: {}, 收件人数量: {}", mailMsg.getTitle(), tos.size());
            if (CollectionUtils.isEmpty(mailFiles)) {
                MailUtil.send(mailAccount, tos, ccList, null, mailMsg.getTitle(), mailMsg.getContent(), true);
            } else {
                MailUtil.send(mailAccount, tos, ccList, null, mailMsg.getTitle(), mailMsg.getContent(), true, mailFiles.toArray(new File[0]));
            }
            log.info("邮件发送成功，收件人: {}", tos);
            sendResult.setSuccess(true);

        } catch (Exception e) {
            sendResult.setSuccess(false);
            sendResult.setInfo(e.getMessage());
            log.error("邮件发送失败，错误信息: {}", e.getMessage(), e);
            log.error(ExceptionUtils.getStackTrace(e));
        }

        return sendResult;
    }

    private void getMailFiles(String files, List<File> mailFiles) throws IOException {
        if(StringUtils.isNotEmpty(files)) {
            JSONObject jsonObject = JSONObject.parseObject(files);
            String filePath = jsonObject.getString("filePath");
            String fileName = jsonObject.getString("fileName");
            
            if(StringUtils.isBlank(filePath)) {
                log.warn("文件路径为空，跳过文件下载");
                return;
            }
            
            log.info("开始下载邮件附件，文件路径: {}, 文件名: {}", filePath, fileName);
            URL url = new URL(filePath);
            HttpURLConnection httpURLConnection = null;
            BufferedInputStream bin = null;
            FileOutputStream out = null;
            
            try {
                URLConnection urlConnection = url.openConnection();
                httpURLConnection = (HttpURLConnection) urlConnection;
                // 设置连接超时为30秒
                httpURLConnection.setConnectTimeout(1000 * 30);
                // 设置读取超时为60秒
                httpURLConnection.setReadTimeout(1000 * 60);
                httpURLConnection.setRequestMethod("GET");
                httpURLConnection.setRequestProperty("Charset", "UTF-8");
                // 设置用户代理，避免某些服务器拒绝请求
                httpURLConnection.setRequestProperty("User-Agent", "Mozilla/5.0");
                
                log.debug("尝试连接文件服务器: {}", filePath);
                httpURLConnection.connect();
                
                int responseCode = httpURLConnection.getResponseCode();
                if (responseCode != HttpURLConnection.HTTP_OK) {
                    throw new IOException("文件下载失败，HTTP响应码: " + responseCode);
                }
                
                String path = mailAnnexDir + File.separatorChar + fileName;
                log.info("存储位置目录：{}", path);
                File file = new File(path);
                
                // 校验文件夹目录是否存在，不存在就创建一个目录
                if (!file.getParentFile().exists()) {
                    file.getParentFile().mkdirs();
                }
                
                bin = new BufferedInputStream(httpURLConnection.getInputStream());
                out = new FileOutputStream(file);
                
                int size = 0;
                byte[] b = new byte[20480];
                long totalBytes = 0;
                //把输入流的文件读取到字节数据b中，然后输出到指定目录的文件
                while ((size = bin.read(b)) != -1) {
                    out.write(b, 0, size);
                    totalBytes += size;
                }
                out.flush();
                
                log.info("文件下载成功，文件名: {}, 大小: {} bytes", fileName, totalBytes);
                mailFiles.add(file);
                
            } catch (IOException e) {
                log.error("下载邮件附件失败，文件路径: {}, 错误信息: {}", filePath, e.getMessage(), e);
                throw e;
            } finally {
                // 确保资源被正确关闭
                if (bin != null) {
                    try {
                        bin.close();
                    } catch (IOException e) {
                        log.warn("关闭输入流失败: {}", e.getMessage());
                    }
                }
                if (out != null) {
                    try {
                        out.close();
                    } catch (IOException e) {
                        log.warn("关闭输出流失败: {}", e.getMessage());
                    }
                }
                if (httpURLConnection != null) {
                    httpURLConnection.disconnect();
                }
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
