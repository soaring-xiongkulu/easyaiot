package com.basiclab.iot.node.util;

import cn.hutool.core.util.StrUtil;
import com.jcraft.jsch.ChannelExec;
import com.jcraft.jsch.JSch;
import com.jcraft.jsch.JSchException;
import com.jcraft.jsch.Session;
import lombok.extern.slf4j.Slf4j;

import java.io.ByteArrayOutputStream;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.util.Properties;

@Slf4j
public final class SshClientUtil {

    private static final int CONNECT_TIMEOUT_MS = 10000;
    private static final int COMMAND_TIMEOUT_MS = 15000;

    private SshClientUtil() {
    }

    public static boolean testConnection(String host, int port, String username,
                                         String authType, String password, String privateKey) {
        Session session = null;
        try {
            session = openSession(host, port, username, authType, password, privateKey);
            session.connect(CONNECT_TIMEOUT_MS);
            return session.isConnected();
        } catch (Exception e) {
            log.warn("SSH 连接测试失败: {}@{}:{} - {}", username, host, port, e.getMessage());
            return false;
        } finally {
            disconnect(session);
        }
    }

    public static String executeCommand(String host, int port, String username,
                                        String authType, String password, String privateKey,
                                        String command) throws JSchException {
        Session session = null;
        ChannelExec channel = null;
        try {
            session = openSession(host, port, username, authType, password, privateKey);
            session.connect(CONNECT_TIMEOUT_MS);
            channel = (ChannelExec) session.openChannel("exec");
            channel.setCommand(command);
            channel.setInputStream(null);
            ByteArrayOutputStream output = new ByteArrayOutputStream();
            ByteArrayOutputStream error = new ByteArrayOutputStream();
            channel.setOutputStream(output);
            channel.setErrStream(error);
            channel.connect(COMMAND_TIMEOUT_MS);
            while (!channel.isClosed()) {
                Thread.sleep(100);
            }
            if (channel.getExitStatus() != 0) {
                throw new JSchException("命令执行失败: " + error.toString(StandardCharsets.UTF_8));
            }
            return output.toString(StandardCharsets.UTF_8);
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
            throw new JSchException("SSH 命令被中断", e);
        } finally {
            if (channel != null) {
                channel.disconnect();
            }
            disconnect(session);
        }
    }

    public static boolean installPublicKey(String host, int port, String username,
                                           String authType, String password, String privateKey,
                                           String publicKeyContent) {
        String escapedKey = publicKeyContent.replace("'", "'\\''");
        String command = "mkdir -p ~/.ssh && chmod 700 ~/.ssh && "
                + "grep -qxF '" + escapedKey + "' ~/.ssh/authorized_keys 2>/dev/null "
                + "|| echo '" + escapedKey + "' >> ~/.ssh/authorized_keys && "
                + "chmod 600 ~/.ssh/authorized_keys && echo OK";
        try {
            String result = executeCommand(host, port, username, authType, password, privateKey, command);
            return result != null && result.contains("OK");
        } catch (Exception e) {
            log.warn("写入 SSH 公钥失败: {}@{} - {}", username, host, e.getMessage());
            return false;
        }
    }

    private static Session openSession(String host, int port, String username,
                                       String authType, String password, String privateKey) throws JSchException {
        JSch jsch = new JSch();
        if ("private_key".equals(authType) && StrUtil.isNotBlank(privateKey)) {
            jsch.addIdentity("node-key", privateKey.getBytes(StandardCharsets.UTF_8), null, null);
        }
        Session session = jsch.getSession(username, host, port);
        if (!"private_key".equals(authType) && StrUtil.isNotBlank(password)) {
            session.setPassword(password);
        }
        Properties config = new Properties();
        config.put("StrictHostKeyChecking", "no");
        session.setConfig(config);
        return session;
    }

    private static void disconnect(Session session) {
        if (session != null && session.isConnected()) {
            session.disconnect();
        }
    }

}
