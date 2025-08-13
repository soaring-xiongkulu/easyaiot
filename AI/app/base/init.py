# 子模块中想初始化啥，就在对应函数上加一个装饰器@init，可以在初始化函数中操作数据库（因为初始化环境在app_context内，且会先将表创建出来再执行初始化）
_init_funcs = []

def init(init_func: callable):
    _init_funcs.append(init_func)
    return init_func

def init_all():
    global _init_funcs
    for init_func in _init_funcs:
        init_func()
    del _init_funcs
