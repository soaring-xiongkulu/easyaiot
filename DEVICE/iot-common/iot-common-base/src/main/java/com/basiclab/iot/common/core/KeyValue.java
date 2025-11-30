package com.basiclab.iot.common.core;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;
import lombok.experimental.Accessors;

import java.io.Serializable;

/**
 * Key Value 的键值对
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
@Accessors(chain = true)
public class KeyValue<K, V> implements Serializable {

    private K key;
    private V value;

}
