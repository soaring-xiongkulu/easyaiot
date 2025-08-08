package com.basiclab.iot.rule;

import com.google.common.collect.Lists;
import com.basiclab.iot.common.utils.SpelComparisonUtil;
import org.junit.jupiter.api.Test;
import org.springframework.expression.ExpressionParser;
import org.springframework.expression.spel.standard.SpelExpressionParser;
import org.springframework.expression.spel.support.StandardEvaluationContext;

import java.util.ArrayList;
import java.util.List;

/**
 * @author IoT
 * @desc
 * @created 2024-07-31
 */
public class CompareTest {

    @Test
    public void testCompareStr() {
        boolean compare1 = SpelComparisonUtil.compare("-3.00000003e-03", "==", "-3.00000003e-03");
        System.out.println("比较字符串: " + compare1);

        boolean compare2 = SpelComparisonUtil.compare(true, "and", false);
        System.out.println("比较与关系: " + compare2);

        boolean compare3 = SpelComparisonUtil.compare(true, "or", false);
        System.out.println("比较或关系: " + compare3);

        boolean compare4 = SpelComparisonUtil.compare(22, ">=", 11);
        System.out.println("比较大于等于关系: " + compare4);

        boolean compare5 = SpelComparisonUtil.compare(22, "<=", 11);
        System.out.println("比较小于等于关系: " + compare5);

        boolean compare6 = SpelComparisonUtil.compare(22, "==", 11);
        System.out.println("比较等等于关系: " + compare6);

        boolean compare7 = SpelComparisonUtil.compare(22, ">", 11);
        System.out.println("比较大于关系: " + compare7);

        boolean compare8 = SpelComparisonUtil.compare(22, "<", 11);
        System.out.println("比较小于关系: " + compare8);

        ArrayList<Object> list = Lists.newArrayList();
        list.add("11");
        list.add("12");
        boolean compare9 = SpelComparisonUtil.compare(list, "in", "12");
        System.out.println("比较包含关系: " + compare9);


    }

    @Test
    @SuppressWarnings("unchecked")
    public void test1() {
        // create an array of integers
        List<Integer> primes = Lists.newArrayList(2, 3, 5, 7, 11, 13, 17);
        ExpressionParser parser = new SpelExpressionParser();
        StandardEvaluationContext context = new StandardEvaluationContext();
        context.setVariable("primes", primes);
        List<Integer> primesGreaterThanTen = (List<Integer>) parser.parseExpression(
                //.?[] 用来从集合中选择符合特定条件的元素。在这种情况下，它会遍历 #primes 集合中的每一个元素
                //primes集合中大于10的数据
                "#primes.?[#this==10]").getValue(context);
        System.out.println(primesGreaterThanTen);
    }

    @Test
    public void test2() {


    }


}
