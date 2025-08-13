package com.basiclab.iot.common.utils;

import com.alibaba.fastjson.JSON;
import com.alibaba.fastjson.TypeReference;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;

/**
 * @author chengmo on 2020/7/16
 */
public class JSONUtils {

    public static <T> Map<String, Object> toMap(T bean) {
        String text = JSON.toJSONString(bean);
        return JSON.parseObject(text, new TypeReference<Map<String, Object>>() {
        });
    }

    public static <T> List<Map<String, Object>> toListMap(List<T> beanList) {
        String text = JSON.toJSONString(beanList);
        return JSON.parseObject(text, new TypeReference<List<Map<String, Object>>>() {
        });
    }

    public static Map<String, Object> jsonToMap(String json) {
        return JSON.parseObject(json, new TypeReference<Map<String, Object>>() {
        });
    }

    public static List<Map<String, Object>> jsonToListMap(String json) {
        return JSON.parseObject(json, new TypeReference<List<Map<String, Object>>>() {
        });
    }

    public static List<Map<String, Object>> toListMap(Object obj) {
        String json = JSON.toJSONString(obj);
        return JSON.parseObject(json, new TypeReference<List<Map<String, Object>>>() {
        });
    }

    public static <From, To> To copy(From bean, Class<To> toClass) {
        return JSON.parseObject(JSON.toJSONString(bean), toClass);
    }

    public static <From, To> List<To> copy(List<From> beanList, Class<To> toClass) {
        List<To> toBeanList = new ArrayList<>();
        beanList.stream().forEach(e -> {
            toBeanList.add(copy(e, toClass));
        });
        return toBeanList;
    }

    public static <T> void println(T object) {
        System.out.println(JSON.toJSONString(object, true));
    }

    /**
     * json格式的字符串, 进行打印日志格式化输出
     * @param json
     * @return
     */
    public static String jsonFormat(String json){
        //如果已經存在格式化的json，則不需要處理
        if(json.indexOf("\n")>0||json.indexOf("\t")>0){
            return json;
        }
        int level = 0;
        //存放格式化的json字符串
        StringBuffer jsonForMatStr = new StringBuffer();
        for(int index=0;index<json.length();index++)//将字符串中的字符逐个按行输出
        {
            //获取s中的每个字符
            char c = json.charAt(index);

            //level大于0并且jsonForMatStr中的最后一个字符为\n,jsonForMatStr加入\t
            if (level > 0 && '\n' == jsonForMatStr.charAt(jsonForMatStr.length() - 1)) {
                jsonForMatStr.append(getLevelStr(level));
            }
            //遇到"{"和"["要增加空格和换行，遇到"}"和"]"要减少空格，以对应，遇到","要换行
            switch (c) {
                case '{':
                case '[':
                    jsonForMatStr.append(c + "\n");
                    level++;
                    break;
                case ',':
                    jsonForMatStr.append(c + "\n");
                    break;
                case '}':
                case ']':
                    jsonForMatStr.append("\n");
                    level--;
                    jsonForMatStr.append(getLevelStr(level));
                    jsonForMatStr.append(c);
                    break;
                default:
                    jsonForMatStr.append(c);
                    break;
            }
        }
        return jsonForMatStr.toString();
    }

    private static String getLevelStr(int level) {
        StringBuffer levelStr = new StringBuffer();
        for (int levelI = 0; levelI < level; levelI++) {
            levelStr.append("\t");
        }
        return levelStr.toString();
    }
}
