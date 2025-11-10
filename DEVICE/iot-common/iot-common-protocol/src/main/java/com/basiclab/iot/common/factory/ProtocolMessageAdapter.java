package com.basiclab.iot.common.factory;

import cn.hutool.core.bean.BeanUtil;
import com.alibaba.fastjson.JSON;
import com.alibaba.fastjson.JSONObject;
import com.alibaba.fastjson.TypeReference;
import com.basiclab.iot.common.model.EncryptionDetailsDTO;
import com.basiclab.iot.common.model.ProtocolDataMessageDTO;
import com.basiclab.iot.common.utils.ProtocolMessageSignatureVerifierUtils;
import com.basiclab.iot.common.utils.ProtocolRegexTopicVariableExtractorUtils;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Component;

import java.util.Map;

/**
 * @program: EasyAIoT
 * @description: 协议信息适配器
 * @packagename: com.basiclab.iot.mqtt.handler
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 * @date: 2023-05-30 15:08
 **/
@Slf4j
@Component
public class ProtocolMessageAdapter {

    public boolean validateProtocolData(String body) {
        return ProtocolMessageSignatureVerifierUtils.validateProtocolData(body);
    }

    public Map<String, String> extractVariables(String topic) {
        return ProtocolRegexTopicVariableExtractorUtils.extractVariables(topic);
    }

    public ProtocolDataMessageDTO parseProtocolDataMessage(String body) {
        return BeanUtil.toBean(JSON.parseObject(body), ProtocolDataMessageDTO.class);
    }

    public String decryptMessage(String body, EncryptionDetailsDTO encryptionDetailsDTO) throws Exception {
        String signKey = encryptionDetailsDTO.getSignKey();
        String encryptKey = encryptionDetailsDTO.getEncryptKey();
        String encryptVector = encryptionDetailsDTO.getEncryptVector();
        return ProtocolMessageSignatureVerifierUtils.decryptMessage(body, signKey, encryptKey, encryptVector);
    }

    public <T> ProtocolDataMessageDTO<T> buildResponse(ProtocolDataMessageDTO<T> protocolDataMessageDTO,
                                                       String resultDataBody, EncryptionDetailsDTO encryptionDetailsDTO) throws Exception {
        String signKey = encryptionDetailsDTO.getSignKey();
        String encryptKey = encryptionDetailsDTO.getEncryptKey();
        String encryptVector = encryptionDetailsDTO.getEncryptVector();
        //数据加密签名处理
        String dataBody = ProtocolMessageSignatureVerifierUtils.encryptMessage(resultDataBody, protocolDataMessageDTO.getHead().getCipherFlag(), signKey, encryptKey,
                encryptVector);
        //JSON字符串转换为对象
        protocolDataMessageDTO = JSON.parseObject(dataBody, new TypeReference<ProtocolDataMessageDTO>() {
        });


        return protocolDataMessageDTO;
    }

    /**
     * 将请求的json进行处理  进行加密处理
     *
     * @param resultDataBody
     * @param encryptionDetailsDTO
     * @param <T>
     * @return
     * @throws Exception
     */
    public <T> ProtocolDataMessageDTO buildResponse(String resultDataBody, EncryptionDetailsDTO encryptionDetailsDTO) throws Exception {
        String signKey = encryptionDetailsDTO.getSignKey();
        String encryptKey = encryptionDetailsDTO.getEncryptKey();
        String encryptVector = encryptionDetailsDTO.getEncryptVector();
        //数据加密签名处理
        String dataBody = ProtocolMessageSignatureVerifierUtils.encryptMessage(resultDataBody, encryptionDetailsDTO.getCipherFlag(), signKey, encryptKey,
                encryptVector);
        //JSON字符串转换为对象
        return JSONObject.parseObject(dataBody, ProtocolDataMessageDTO.class);
    }
}
