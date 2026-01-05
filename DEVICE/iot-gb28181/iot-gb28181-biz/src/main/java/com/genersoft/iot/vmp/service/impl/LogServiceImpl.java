package com.genersoft.iot.vmp.service.impl;

import com.genersoft.iot.vmp.conf.exception.ControllerException;
import com.genersoft.iot.vmp.service.ILogService;
import com.genersoft.iot.vmp.service.bean.LogFileInfo;
import com.genersoft.iot.vmp.utils.DateUtil;
import com.genersoft.iot.vmp.vmanager.bean.ErrorCode;
import lombok.extern.slf4j.Slf4j;
import org.apache.logging.log4j.LogManager;
import org.apache.logging.log4j.core.Appender;
import org.apache.logging.log4j.core.LoggerContext;
import org.apache.logging.log4j.core.appender.FileAppender;
import org.apache.logging.log4j.core.appender.RollingFileAppender;
import org.apache.logging.log4j.core.config.Configuration;
import org.springframework.stereotype.Service;

import java.io.*;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;

@Service
@Slf4j
public class LogServiceImpl implements ILogService {

    @Override
    public List<LogFileInfo> queryList(String query, String startTime, String endTime) {
        File logFile = getLogDir();
        if (logFile == null || !logFile.exists()) {
            throw new ControllerException(ErrorCode.ERROR100.getCode(), "获取日志文件目录失败");
        }
        File[] files = logFile.listFiles();
        List<LogFileInfo> result = new ArrayList<>();
        if (files == null || files.length == 0) {
            return result;
        }

        // 读取文件创建时间作为开始时间，修改时间为结束时间
        Long startTimestamp = null;
        if (startTime != null) {
            startTimestamp = DateUtil.yyyy_MM_dd_HH_mm_ssToTimestampMs(startTime);
        }
        Long endTimestamp = null;
        if (endTime != null) {
            endTimestamp = DateUtil.yyyy_MM_dd_HH_mm_ssToTimestampMs(endTime);
        }
        for (File file : files) {
            LogFileInfo logFileInfo = new LogFileInfo();
            logFileInfo.setFileName(file.getName());
            logFileInfo.setFileSize(file.length());
            if (query != null && !file.getName().contains(query)) {
                continue;
            }
            try {
                Long[] fileAttributes = getFileAttributes(file);
                if (fileAttributes == null) {
                    continue;
                }
                long startTimestampForFile  = fileAttributes[0];
                long endTimestampForFile  = fileAttributes[1];
                logFileInfo.setStartTime(startTimestampForFile);
                logFileInfo.setEndTime(endTimestampForFile);
                if (startTimestamp != null && startTimestamp > startTimestampForFile) {
                    continue;
                }
                if (endTimestamp != null && endTimestamp < endTimestampForFile) {
                    continue;
                }
            } catch (IOException e) {
                log.error("[读取日志文件列表] 获取创建时间和修改时间失败", e);
                continue;
            }
            result.add(logFileInfo);

        }
        result.sort((o1, o2) -> o2.getStartTime().compareTo(o1.getStartTime()));
        return result;
    }

    private File getLogDir() {
        try {
            // 获取 Log4j2 配置，LoggerContext 由 LogManager 管理，不需要手动关闭
            org.apache.logging.log4j.spi.LoggerContext loggerContext = LogManager.getContext(false);
            if (loggerContext instanceof LoggerContext) {
                Configuration configuration = ((LoggerContext) loggerContext).getConfiguration();
                
                // 遍历所有 appender，查找文件 appender
                Map<String, Appender> appenders = configuration.getAppenders();
                for (Appender appender : appenders.values()) {
                    if (appender instanceof FileAppender) {
                        FileAppender fileAppender = (FileAppender) appender;
                        String fileName = fileAppender.getFileName();
                        if (fileName != null) {
                            File logFile = new File(fileName);
                            return logFile.getParentFile();
                        }
                    } else if (appender instanceof RollingFileAppender) {
                        RollingFileAppender rollingFileAppender = (RollingFileAppender) appender;
                        String fileName = rollingFileAppender.getFileName();
                        if (fileName != null) {
                            File logFile = new File(fileName);
                            return logFile.getParentFile();
                        }
                    }
                }
            }
        } catch (Exception e) {
            log.warn("[获取日志目录] 从 Log4j2 配置获取失败，使用默认目录", e);
        }
        
        // 如果都不存在，使用默认日志目录
        return new File(System.getProperty("user.home"), "logs");
    }

    Long[] getFileAttributes(File file) throws IOException {
        try (BufferedReader bufferedReader = new BufferedReader(new FileReader(file))) {
            String startLine = bufferedReader.readLine();
            if (startLine == null) {
                return null;
            }
            String startTime = startLine.substring(0, 19);

            // 最后一行的开头不一定是时间
            //        String lastLine = "";
            //        try (ReversedLinesFileReader reversedLinesReader = new ReversedLinesFileReader(file, Charset.defaultCharset())) {
            //            lastLine = reversedLinesReader.readLine();
            //        } catch (Exception e) {
            //            log.error("file read error, msg:{}", e.getMessage(), e);
            //        }
            //        String endTime = lastLine.substring(0, 19);
            return new Long[]{DateUtil.yyyy_MM_dd_HH_mm_ssToTimestampMs(startTime), file.lastModified()};
        }
    }

    @Override
    public File getFileByName(String fileName) {
        File logDir = getLogDir();

        return new File(logDir, fileName);
    }
}
