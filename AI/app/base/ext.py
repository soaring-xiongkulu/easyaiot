import json
from enum import Enum
from flask_sqlalchemy import SQLAlchemy

from app.base.app import app


db = SQLAlchemy(app)

class BaseModel(db.Model):
    __abstract__ = True
    _scope_type_map = {}

    class ScopeType(Enum):
        ORIGIN = 0
        JSON = 1
        DATETIME = 2
    
    # 用这个装饰一个类里的特殊类型的字段，直接打到类上就行
    @staticmethod
    def Scope(**scopes):
        def deco(cls):
            cls._scope_type_map = scopes
            return cls
        return deco
    
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

    # 两种访问方式：
    # 用m.x访问，返回sqlalchemy的类型（这种方式不能覆盖）
    # 用m[x]访问，返回类型映射后的变量类型
    def __getitem__(self, name):
        value = getattr(self, name)
        if name in self.__table__.columns and value is not None:
            if scope_type:= self._scope_type_map.get(name):
                if scope_type == self.ScopeType.JSON:
                    value = json.loads(value)
                elif scope_type == self.ScopeType.DATETIME:
                    value = value.strftime('%Y-%m-%d %H:%M:%S')
        return value
    
    # 支持m[x]赋值
    def __setitem__(self, name, value):
        setattr(self, name, value)

    def __setattr__(self, name, value):
        if name in self.__table__.columns and value is not None:
            if scope_type:= self._scope_type_map.get(name):
                if scope_type == self.ScopeType.JSON:
                    value = json.dumps(value, ensure_ascii=False)
        super().__setattr__(name, value)
    
    # 将字段注册一个映射，这样可以设置和获取时对某些字段进行自动转换
    @staticmethod
    def _get_scope_type() -> dict:
        return None

    def to_dict(self) -> dict:
        return {c.name: self[c.name] for c in self.__table__.columns}
