package com.basiclab.iot.common.exception.user;

import com.basiclab.iot.common.exception.BaseException;

/**
 * 用户信息异常类
 * 
 * @author EasyIoT
 */
public class UserException extends BaseException
{
    private static final long serialVersionUID = 1L;

    public UserException(String code, Object[] args)
    {
        super("user", code, args, null);
    }
}
