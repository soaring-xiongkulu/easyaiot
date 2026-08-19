package com.basiclab.iot.node.util;

import com.jcraft.jsch.ChannelExec;
import com.jcraft.jsch.ChannelSftp;
import com.jcraft.jsch.JSch;
import com.jcraft.jsch.JSchException;
import com.jcraft.jsch.Session;
import com.jcraft.jsch.SftpException;
import lombok.Getter;
import lombok.extern.slf4j.Slf4j;

import java.io.ByteArrayOutputStream;
import java.io.File;
import java.io.FileInputStream;
import java.io.IOException;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.util.Properties;

@Slf4j
public class SshSessionHelper implements AutoCloseable {

    private static final int CONNECT_TIMEOUT_MS = 15000;

    @Getter
    private final Session session;

    private SshSessionHelper(Session session) {
        this.session = session;
    }

    public static SshSessionHelper connect(String host, int port, String username,
                                           String authType, String password, String privateKey) throws JSchException {
        JSch jsch = new JSch();
        if ("private_key".equals(authType) && privateKey != null && !privateKey.isBlank()) {
            jsch.addIdentity("node-key", privateKey.getBytes(StandardCharsets.UTF_8), null, null);
        }
        Session session = jsch.getSession(username, host, port);
        if (!"private_key".equals(authType) && password != null && !password.isBlank()) {
            session.setPassword(password);
        }
        Properties config = new Properties();
        config.put("StrictHostKeyChecking", "no");
        session.setConfig(config);
        session.connect(CONNECT_TIMEOUT_MS);
        return new SshSessionHelper(session);
    }

    public SshExecResult exec(String command, int timeoutMs) throws JSchException, InterruptedException {
        ChannelExec channel = null;
        try {
            channel = (ChannelExec) session.openChannel("exec");
            // RUNTIME 等组件若把专用 lib 写进 profile.d 的 LD_LIBRARY_PATH，sudo 会加载失败
            channel.setCommand("unset LD_LIBRARY_PATH LD_PRELOAD; " + command);
            channel.setInputStream(null);
            ByteArrayOutputStream output = new ByteArrayOutputStream();
            ByteArrayOutputStream error = new ByteArrayOutputStream();
            channel.setOutputStream(output);
            channel.setErrStream(error);
            channel.connect(timeoutMs);
            long deadline = System.currentTimeMillis() + timeoutMs;
            while (!channel.isClosed()) {
                if (System.currentTimeMillis() > deadline) {
                    throw new JSchException("SSH 命令执行超时");
                }
                Thread.sleep(200);
            }
            return new SshExecResult(channel.getExitStatus(),
                    output.toString(StandardCharsets.UTF_8),
                    error.toString(StandardCharsets.UTF_8));
        } finally {
            if (channel != null) {
                channel.disconnect();
            }
        }
    }

    public void ensureRemoteDir(String remoteDir) throws JSchException, SftpException {
        ChannelSftp sftp = null;
        try {
            sftp = (ChannelSftp) session.openChannel("sftp");
            sftp.connect(CONNECT_TIMEOUT_MS);
            String[] parts = remoteDir.split("/");
            StringBuilder path = new StringBuilder();
            for (String part : parts) {
                if (part.isEmpty()) {
                    continue;
                }
                path.append('/').append(part);
                try {
                    sftp.cd(path.toString());
                } catch (SftpException e) {
                    sftp.mkdir(path.toString());
                }
            }
        } finally {
            if (sftp != null) {
                sftp.disconnect();
            }
        }
    }

    public void uploadFile(String localPath, String remotePath) throws JSchException, SftpException, IOException {
        File file = new File(localPath);
        if (!file.isFile()) {
            throw new SftpException(ChannelSftp.SSH_FX_NO_SUCH_FILE, "本地文件不存在: " + localPath);
        }
        ChannelSftp sftp = null;
        try {
            sftp = (ChannelSftp) session.openChannel("sftp");
            sftp.connect(CONNECT_TIMEOUT_MS);
            int lastSlash = remotePath.lastIndexOf('/');
            if (lastSlash > 0) {
                ensureRemoteDir(remotePath.substring(0, lastSlash));
            }
            try (InputStream in = new FileInputStream(file)) {
                sftp.put(in, remotePath);
            }
        } finally {
            if (sftp != null) {
                sftp.disconnect();
            }
        }
    }

    /**
     * 递归上传本地目录到远程（跳过 __pycache__、.env、logs 等）。
     *
     * @return 上传的文件数
     */
    public int uploadDirectoryRecursive(
            File localDir,
            String remoteDir,
            java.util.function.Predicate<String> skipDir,
            java.util.function.Predicate<String> skipFile) throws JSchException, SftpException, IOException {
        if (localDir == null || !localDir.isDirectory()) {
            throw new SftpException(ChannelSftp.SSH_FX_NO_SUCH_FILE, "本地目录不存在: " + localDir);
        }
        ensureRemoteDir(remoteDir);
        int count = 0;
        File[] children = localDir.listFiles();
        if (children == null) {
            return 0;
        }
        for (File child : children) {
            String name = child.getName();
            if (child.isDirectory()) {
                if (skipDir != null && skipDir.test(name)) {
                    continue;
                }
                count += uploadDirectoryRecursive(
                        child,
                        remoteDir + "/" + name,
                        skipDir,
                        skipFile);
            } else if (child.isFile()) {
                if (skipFile != null && skipFile.test(name)) {
                    continue;
                }
                uploadFile(child.getAbsolutePath(), remoteDir + "/" + name);
                count++;
            }
        }
        return count;
    }

    /** 列出远程目录条目（不含 . / ..） */
    @SuppressWarnings("unchecked")
    public java.util.List<SftpEntry> listDir(String remoteDir) throws JSchException, SftpException {
        ChannelSftp sftp = null;
        try {
            sftp = (ChannelSftp) session.openChannel("sftp");
            sftp.connect(CONNECT_TIMEOUT_MS);
            java.util.Vector<ChannelSftp.LsEntry> vector = sftp.ls(remoteDir);
            java.util.List<SftpEntry> result = new java.util.ArrayList<>();
            if (vector == null) {
                return result;
            }
            for (ChannelSftp.LsEntry entry : vector) {
                String name = entry.getFilename();
                if (".".equals(name) || "..".equals(name)) {
                    continue;
                }
                com.jcraft.jsch.SftpATTRS attrs = entry.getAttrs();
                boolean dir = attrs != null && attrs.isDir();
                long size = attrs != null ? attrs.getSize() : 0L;
                long mtimeSec = attrs != null ? attrs.getMTime() : 0L;
                result.add(new SftpEntry(name, dir, size, mtimeSec));
            }
            result.sort((a, b) -> {
                if (a.directory != b.directory) {
                    return a.directory ? -1 : 1;
                }
                return a.name.compareToIgnoreCase(b.name);
            });
            return result;
        } finally {
            if (sftp != null) {
                sftp.disconnect();
            }
        }
    }

    /** 读取远程文件到内存（调用方需先校验大小） */
    public byte[] downloadBytes(String remotePath) throws JSchException, SftpException, IOException {
        ChannelSftp sftp = null;
        try {
            sftp = (ChannelSftp) session.openChannel("sftp");
            sftp.connect(CONNECT_TIMEOUT_MS);
            try (InputStream in = sftp.get(remotePath);
                 ByteArrayOutputStream out = new ByteArrayOutputStream()) {
                byte[] buf = new byte[8192];
                int n;
                while ((n = in.read(buf)) >= 0) {
                    out.write(buf, 0, n);
                }
                return out.toByteArray();
            }
        } finally {
            if (sftp != null) {
                sftp.disconnect();
            }
        }
    }

    /** 远程文件属性；不存在时返回 null */
    public SftpEntry stat(String remotePath) throws JSchException, SftpException {
        ChannelSftp sftp = null;
        try {
            sftp = (ChannelSftp) session.openChannel("sftp");
            sftp.connect(CONNECT_TIMEOUT_MS);
            com.jcraft.jsch.SftpATTRS attrs = sftp.stat(remotePath);
            String name = remotePath;
            int slash = remotePath.lastIndexOf('/');
            if (slash >= 0 && slash < remotePath.length() - 1) {
                name = remotePath.substring(slash + 1);
            }
            return new SftpEntry(name, attrs.isDir(), attrs.getSize(), attrs.getMTime());
        } catch (SftpException e) {
            if (e.id == ChannelSftp.SSH_FX_NO_SUCH_FILE) {
                return null;
            }
            throw e;
        } finally {
            if (sftp != null) {
                sftp.disconnect();
            }
        }
    }

    public void mkdir(String remoteDir) throws JSchException, SftpException {
        ChannelSftp sftp = null;
        try {
            sftp = (ChannelSftp) session.openChannel("sftp");
            sftp.connect(CONNECT_TIMEOUT_MS);
            sftp.mkdir(remoteDir);
        } finally {
            if (sftp != null) {
                sftp.disconnect();
            }
        }
    }

    public void rename(String fromPath, String toPath) throws JSchException, SftpException {
        ChannelSftp sftp = null;
        try {
            sftp = (ChannelSftp) session.openChannel("sftp");
            sftp.connect(CONNECT_TIMEOUT_MS);
            sftp.rename(fromPath, toPath);
        } finally {
            if (sftp != null) {
                sftp.disconnect();
            }
        }
    }

    public void uploadBytes(String remotePath, byte[] content) throws JSchException, SftpException, IOException {
        if (content == null) {
            content = new byte[0];
        }
        ChannelSftp sftp = null;
        try {
            sftp = (ChannelSftp) session.openChannel("sftp");
            sftp.connect(CONNECT_TIMEOUT_MS);
            int lastSlash = remotePath.lastIndexOf('/');
            if (lastSlash > 0) {
                ensureRemoteDir(remotePath.substring(0, lastSlash));
            }
            try (java.io.ByteArrayInputStream in = new java.io.ByteArrayInputStream(content)) {
                sftp.put(in, remotePath);
            }
        } finally {
            if (sftp != null) {
                sftp.disconnect();
            }
        }
    }

    /** 删除文件或递归删除目录 */
    public void deleteRecursive(String remotePath) throws JSchException, SftpException {
        ChannelSftp sftp = null;
        try {
            sftp = (ChannelSftp) session.openChannel("sftp");
            sftp.connect(CONNECT_TIMEOUT_MS);
            deleteRecursiveInternal(sftp, remotePath);
        } finally {
            if (sftp != null) {
                sftp.disconnect();
            }
        }
    }

    @SuppressWarnings("unchecked")
    private void deleteRecursiveInternal(ChannelSftp sftp, String remotePath) throws SftpException {
        com.jcraft.jsch.SftpATTRS attrs = sftp.stat(remotePath);
        if (attrs.isDir()) {
            java.util.Vector<ChannelSftp.LsEntry> vector = sftp.ls(remotePath);
            if (vector != null) {
                for (ChannelSftp.LsEntry entry : vector) {
                    String name = entry.getFilename();
                    if (".".equals(name) || "..".equals(name)) {
                        continue;
                    }
                    String child = remotePath.endsWith("/") ? remotePath + name : remotePath + "/" + name;
                    deleteRecursiveInternal(sftp, child);
                }
            }
            sftp.rmdir(remotePath);
        } else {
            sftp.rm(remotePath);
        }
    }

    @Override
    public void close() {
        if (session != null && session.isConnected()) {
            session.disconnect();
        }
    }

    public static final class SftpEntry {
        public final String name;
        public final boolean directory;
        public final long size;
        /** unix epoch seconds */
        public final long mtimeSec;

        public SftpEntry(String name, boolean directory, long size, long mtimeSec) {
            this.name = name;
            this.directory = directory;
            this.size = size;
            this.mtimeSec = mtimeSec;
        }
    }

    public static class SshExecResult {
        private final int exitCode;
        private final String stdout;
        private final String stderr;

        public SshExecResult(int exitCode, String stdout, String stderr) {
            this.exitCode = exitCode;
            this.stdout = stdout;
            this.stderr = stderr;
        }

        public int getExitCode() {
            return exitCode;
        }

        public String getStdout() {
            return stdout;
        }

        public String getStderr() {
            return stderr;
        }

        public String combinedOutput() {
            StringBuilder sb = new StringBuilder();
            if (stdout != null && !stdout.isBlank()) {
                sb.append(stdout.trim());
            }
            if (stderr != null && !stderr.isBlank()) {
                if (sb.length() > 0) {
                    sb.append('\n');
                }
                sb.append(stderr.trim());
            }
            return sb.toString();
        }

        public boolean isSuccess() {
            return exitCode == 0;
        }
    }

}
