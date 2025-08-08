package com.basiclab.iot.common.desensitize.core.regex.handler;

import com.basiclab.iot.common.desensitize.core.regex.annotation.RegexDesensitize;

/**
 * {@link RegexDesensitize} 的正则脱敏处理器
 *
 * @author gaibu
 */
public class DefaultRegexDesensitizationHandler extends AbstractRegexDesensitizationHandler<RegexDesensitize> {

    @Override
    String getRegex(RegexDesensitize annotation) {
        return annotation.regex();
    }

    @Override
    String getReplacer(RegexDesensitize annotation) {
        return annotation.replacer();
    }
}
