package com.basiclab.iot.device.utils;

import lombok.extern.slf4j.Slf4j;
import org.apache.commons.io.IOUtils;
import org.springframework.web.multipart.MultipartFile;

import java.io.*;
import java.net.HttpURLConnection;
import java.net.URL;
import java.util.Base64;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

@Slf4j
public class FileUtil {

    //2.上传文件
    //@Async
    public static void uploadFile(MultipartFile file, String fileUploadPath){

        //1.文件是否为空
        if (file.isEmpty()) {
            throw new IllegalArgumentException("文件为空");
        }

        //2.得到目标文件,断文件父目录是否存在,不存在则新建父目录
        File dest = new File(fileUploadPath);
        if (!dest.getParentFile().exists()) {
            dest.getParentFile().mkdirs();
        }

        //(3).保存文件到本地磁盘,如果文件以及存在则先删除
        try {
            if (dest.exists()) {
                throw new IllegalArgumentException("文件已存在,请修改文件名后再上传:"+fileUploadPath);
                //dest.delete();
            }
            FileOutputStream fo = new FileOutputStream(new File(fileUploadPath));
            InputStream in = file.getInputStream();
            IOUtils.copy(in, fo);
        }catch (IllegalStateException e) {
            e.printStackTrace();
        } catch (IOException e) {
            e.printStackTrace();
        }
    }

    //2.上传文件
    //@Async
    public static void uploadFile(File sourceFile, String destinationPath) {
        File destinationFile = new File(destinationPath);

        try (InputStream inputStream = new FileInputStream(sourceFile);
             OutputStream outputStream = new FileOutputStream(destinationFile)) {
            IOUtils.copy(inputStream, outputStream);
        } catch (FileNotFoundException e) {
            throw new RuntimeException(e);
        } catch (IOException e) {
            throw new RuntimeException(e);
        }
    }


    public static void uploadFile(byte[] bytes, String destinationPath) {
        try {
            File file = new File(destinationPath);
            FileOutputStream fos = new FileOutputStream(file);
            fos.write(bytes);
            fos.close();
        } catch (IOException e) {
            e.printStackTrace();
        }
    }


    //3.把图片文件转为base64
    public static String fileToBase64(byte[] image) {
        Base64.Encoder encoder = Base64.getEncoder();
        byte[] encodeBytes = encoder.encode(image);
        String encodeStr = encoder.encodeToString(encodeBytes);
        return encodeStr;
    }

    //4.把网络图片文件转为base64
    public static String urlFileToBase64(String uri) {
        Base64.Encoder encoder = Base64.getEncoder();
        byte[] encodeBytes = encoder.encode(uri.getBytes());
        String encodeStr = encoder.encodeToString(encodeBytes);
        return encodeStr;
    }

    public static String replaceEnter(String str) {
        String reg = "[\n-\r]";
        Pattern p = Pattern.compile(reg);
        Matcher m = p.matcher(str);
        return m.replaceAll("");
    }


    //4.网络图片转为base64
    public static String encodeImageToBase64(URL url) throws Exception {
        //将图片文件转化为字节数组字符串，并对其进行Base64编码处理
        HttpURLConnection conn ;
        try {
            conn = (HttpURLConnection) url.openConnection();
            //设置请求方式为"GET"
            conn.setRequestMethod("GET");
            //超时响应时间为5秒
            conn.setConnectTimeout(5 * 1000);
            //通过输入流获取图片数据
            InputStream inStream = conn.getInputStream();
            //得到图片的二进制数据，以二进制封装得到数据，具有通用性
            ByteArrayOutputStream outStream = new ByteArrayOutputStream();
            //创建一个Buffer字符串
            byte[] buffer = new byte[1024];
            //每次读取的字符串长度，如果为-1，代表全部读取完毕
            int len = 0;
            //使用一个输入流从buffer里把数据读取出来
            while ((len = inStream.read(buffer)) != -1) {
                //用输出流往buffer里写入数据，中间参数代表从哪个位置开始读，len代表读取的长度
                outStream.write(buffer, 0, len);
            }
            //关闭输入流
            inStream.close();
            byte[] data = outStream.toByteArray();
            //对字节数组Base64编码
            //BASE64Encoder encoder = new BASE64Encoder();
            //String base64 = encoder.encode(data);

            Base64.Encoder encoder = Base64.getEncoder();
            byte[] encodeBytes = encoder.encode(data);
            String base64 = encoder.encodeToString(encodeBytes);

            //System.out.println("网络文件[{}]编码成base64字符串:[{}]"+url.toString()+base64);
            return base64;//返回Base64编码过的字节数组字符串
        } catch (IOException e) {
            e.printStackTrace();
            throw new Exception("图片上传失败!");
        }
    }

    //5.获取文件后缀名
    public static String getSuffix(String originalFilename){
        String suffix = originalFilename.indexOf(".") != -1 ? originalFilename.substring(originalFilename.lastIndexOf("."), originalFilename.length()) : null;
        if (suffix == null) {
            throw new IllegalArgumentException("文件后缀名不正确");
        }
        return suffix;

    }

    //6.获取文件访问全路径
    public static String getCompletePath(String urlStr, String prefix) {
        StringBuffer sb = new StringBuffer();
        String[] fileUrlStr = urlStr.split(",");
        for (int i = 0; i < fileUrlStr.length; i++) {
            if (i == (fileUrlStr.length - 1)) {
                sb.append(prefix + fileUrlStr[i]);
            } else {
                sb.append(prefix + fileUrlStr[i]).append(",");
            }
        }
        return sb.toString();
    }

    //5.检查文件后缀名
    public static String checkSuffix(String originalFilename,String suffixName){
        String suffix = originalFilename.indexOf(".") != -1 ? originalFilename.substring(originalFilename.lastIndexOf("."), originalFilename.length()) : null;
        if (suffix == null) {
            throw new IllegalArgumentException("文件后缀名不正确");
        }

        if (!suffixName.equals(suffix.toLowerCase())) {
            throw new IllegalArgumentException("只能上传"+suffixName+"类型的文件");
        }

        return suffix;
    }

    public static byte[] getBytes(String filePath) {
        byte[] buffer = null;
        try {
            File file = new File(filePath);
            FileInputStream fis = new FileInputStream(file);
            ByteArrayOutputStream bos = new ByteArrayOutputStream(1000);
            byte[] b = new byte[1000];
            int n;
            while ((n = fis.read(b)) != -1) {
                bos.write(b, 0, n);
            }
            fis.close();
            bos.close();
            buffer = bos.toByteArray();
        } catch (FileNotFoundException e) {
            e.printStackTrace();
        } catch (IOException e) {
            e.printStackTrace();
        }
        return buffer;
    }

    public static Boolean checkFileExist(String filename){
        File file = new File(filename);
        boolean exists = file.exists();
        return exists;
    }


/*    public static void main(String[] args) throws Exception {
        String imgFilePath="http://d.hiphotos.baidu.com/image/pic/item/a044ad345982b2b713b5ad7d3aadcbef76099b65.jpg";

        String suffix = getSuffix(imgFilePath);
        System.out.println("suffix:--->"+suffix);
        *//*String base64_str = encodeImageToBase64(new URL(imgFilePath));//将网络图片编码为base64
        //System.out.println(base64_str);
        //Base64Util.b(base64_str,"E:/out.jpg");

        String headerUri = "https://thirdwx.qlogo.cn/mmopen/vi_32/xquaDsYuPhWe3lwgJxBqHl1eYWG6uBBdwuiafG8F9jdicApVzG9sibOx0Bm2KFZ2rQhKLtcdPjO5RIkU7ljI3AMFQ/132";
        String base64 = FileUtil.encodeImageToBase64(new URL(headerUri));
        //System.out.println("base64---》："+base64);*//*
    }*/
}
