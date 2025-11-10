package com.basiclab.iot.common.utils;

import org.springframework.expression.spel.standard.SpelExpression;
import org.springframework.expression.spel.standard.SpelExpressionParser;
import org.springframework.expression.spel.support.StandardEvaluationContext;

import java.util.List;

/**
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 * @desc  spel 表达式比较运算符工具类
 * @created 2025-07-11
 */
public class SpelComparisonUtil {
    private static SpelExpressionParser parser;
    private static StandardEvaluationContext evaluationContext;

    static {
        parser = new SpelExpressionParser();
        evaluationContext = new StandardEvaluationContext();
    }

    /**
     * spel 比较两个对象方法
     * @param leftOperand   源数据
     * @param operator      比较符   > < >= <= != and or  in(包含)
     * @param rightOperand  传递数据
     * @return
     */
    public static boolean compare(Object leftOperand, String operator, Object rightOperand) {
        String expressionString = null;
        if ("in".equals(operator) && leftOperand instanceof List) {
            //包含   leftOperand包含rightOperand
            expressionString = "#left.?[#this==#right]";
            SpelExpression expression = parser.parseRaw(expressionString);
            evaluationContext.setVariable("left", leftOperand);
            evaluationContext.setVariable("right", rightOperand);
            List list = expression.getValue(evaluationContext, List.class);
            assert list != null;
            return !list.isEmpty();
        }else {
            expressionString = String.format("#left %s #right", operator);
            SpelExpression expression = parser.parseRaw(expressionString);
            evaluationContext.setVariable("left", leftOperand);
            evaluationContext.setVariable("right", rightOperand);
            Object value = expression.getValue(evaluationContext);
            return Boolean.TRUE.equals(expression.getValue(evaluationContext, Boolean.class));
        }
    }




}