from flask import has_request_context

from app.base.app import app


class MethodsProxy:
    pass

methods = MethodsProxy()
methods_noerror = MethodsProxy()

def register_method(name: str):
    def deco(func):
        def wrapper(*args, **kwargs):
            if not has_request_context():
                with app.app_context():
                    return func(*args, **kwargs)
            return func(*args, **kwargs)
        def noerror_wrapper(*args, **kwargs):
            try:
                return wrapper(*args, **kwargs)
            except:
                pass
        setattr(methods, name, wrapper)
        setattr(methods_noerror, name, noerror_wrapper)
        return func
    return deco
