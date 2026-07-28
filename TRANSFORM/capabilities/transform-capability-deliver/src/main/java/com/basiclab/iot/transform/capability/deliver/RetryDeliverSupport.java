package com.basiclab.iot.transform.capability.deliver;
import java.time.Duration; import java.util.concurrent.Callable;
/** 有界指数退避重试工具。 */
public final class RetryDeliverSupport { private RetryDeliverSupport(){} public static <T>T execute(Callable<T> call,int attempts,Duration initial) throws Exception { Exception last=null; for(int i=0;i<attempts;i++){try{return call.call();}catch(Exception e){last=e;if(i+1<attempts)Thread.sleep(initial.toMillis()*(1L<<Math.min(i,10)));}} throw last; } }
