package com.basiclab.iot.rule.context;

/**
 * @author EasyAIoT
 * @desc    条件执行上下文
 * @created 2025-07-18
 */
public class ConditionContext {

    private static final ThreadLocal<Context> THREAD_LOCAL = new ThreadLocal<Context>(){
        @Override
        protected Context initialValue() {
            return new Context();
        }
    };

    private static class ConditionContextHolder{
        private final static ConditionContext ACTION_CONTEXT = new ConditionContext();
    }

    public static ConditionContext getInstance(){
        return ConditionContextHolder.ACTION_CONTEXT;
    }

    public Context getContext(){
        return THREAD_LOCAL.get();
    }
    
}
