package com.basiclab.iot.transform.core.spi;

import com.basiclab.iot.transform.core.envelope.TransformEnvelope;
import java.util.Map;

/** N 方系统连接器 SPI。 */
public interface PartyConnector {
    String type();

    void validate(Map<String, Object> contract);

    void deliver(Map<String, Object> contract, TransformEnvelope envelope) throws Exception;
}
