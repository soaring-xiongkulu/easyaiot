package com.basiclab.iot.message.mino.util;

import java.io.File;
import java.io.InputStream;
import java.io.OutputStream;
import java.nio.file.Files;

public class FileUtils {


    public static File inputStreamToFile(InputStream ins, String name) {
        File file = new File(org.apache.commons.io.FileUtils.getTempDirectory() + File.separator + name);
        if (file.exists()) {
            return file;
        }
        try (OutputStream os = Files.newOutputStream(file.toPath()); InputStream inputStream = ins;) {
            int bytesRead;
            int len = 8192;
            byte[] buffer = new byte[len];
            while ((bytesRead = inputStream.read(buffer, 0, len)) != -1) {
                os.write(buffer, 0, bytesRead);
            }
        } catch (Exception e) {
            e.printStackTrace();
        }
        return file;
    }
}
