package com.basiclab.iot.stream.config.exception;

/**
 * @author lin
 */
public class ServiceException extends Exception{
    private String msg;



    public ServiceException(String msg) {
        this.msg = msg;
    }

    public String getMsg() {
        return msg;
    }

    public void setMsg(String msg) {
        this.msg = msg;
    }

    @Override
    public String getMessage() {
        return msg;
    }
}
