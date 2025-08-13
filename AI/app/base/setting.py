import json
from typing import Callable, Any
from pathlib import Path
from distutils.util import strtobool

from app.config import config
from app.base.init import init

_modules = {}

def cast_bool(value: Any) -> bool:
    if type(value) == str:
        value = strtobool(value)
    return bool(value)

def cast_path(value: Any) -> str:
    return str(Path(value).resolve())

class Validator:

    @staticmethod
    def PATH_NOT_EMPTY(path: str):
        if Path(path).exists():
            raise ValueError(f'路径{path}所指向的位置不为空')
    
    @staticmethod
    def FILE_EXISTS(path: str):
        '''该路径存在非目录的文件则验证失败'''
        path = Path(path)
        if path.exists() and path.is_file():
            raise ValueError(f'路径{path}已存在一个同名的非目录文件')

    @staticmethod
    def TIME(time: str):
        try:
            from datetime import datetime
            datetime.strptime(time, '%H:%M:%S')
        except:
            raise ValueError('请传入[时:分:秒]这样的时间格式')
        
    @staticmethod
    def INT_RANGE(begin: int=None, end: int=None):
        def wrapper(value):
            if begin is not None and value < begin or end is not None and value > end:
                raise ValueError(f'数值超出范围[{begin if begin is not None else "-∞"},{end if end is not None else "∞"}]')
        return wrapper
    
    @staticmethod
    def PORT(value):
        if not (value >= 0 and value <= 65535):
            raise ValueError(f'端口号应在[0,65535]之间')

    @staticmethod
    def STR_NOT_EMPTY(value):
        if value == '':
            raise ValueError('字符串不能为空')

class Scope:
    def __init__(
        self, 
        config_name: str,
        type: Any=str,
        validator: Callable[[Any], None]=None, 
        ignore_none: bool=True
    ):
        self.config_name = config_name
        self.type = type
        self.validator = validator
        self.ignore_none = ignore_none

class ModuleSetting:

    def __init__(
        self, 
        scopes: dict[str, Scope], 
        setting_callback: Callable[[dict[str, Any]], None]=None
    ) -> None:
        self._scopes = scopes
        self._setting_callback = setting_callback

        self.name = None

    def check_and_convert(self, settings: dict) -> dict:
        filtered_setting = {}
        for name, value in settings.items():
            scope = self._scopes.get(name)
            if scope is None:
                continue
            
            if value is None:
                if scope.ignore_none:
                    continue
            else:
                try:
                    value = scope.type(value)
                except:
                    raise ValueError(f'{name}参数转换异常，无法将{value}转换为{scope.type.__name__}类型')
                
            config_value = getattr(config, scope.config_name)
            if config_value is not None:
                config_value = scope.type(config_value)
            
            if config_value == value:
                continue

            if value is not None and scope.validator is not None:
                try:
                    scope.validator(value)
                except Exception as e:
                    raise ValueError(f'{name}设置失败，{str(e)}')
            
            filtered_setting[name] = value

        return filtered_setting or None
            
    def update(self, settings: dict):
        for name, value in settings.items():
            setattr(config, self._scopes[name].config_name, value)
    
    def call_callback_func(self, settings):
        if self._setting_callback:
            self._setting_callback(settings)
    
    def get(self):
        return {
            name: getattr(config, scope.config_name) for name, scope in self._scopes.items()
        }
    
def setting(module_name: str):
    def wrapper(setting_func: Callable[[None], ModuleSetting]):
        module_setting = setting_func()
        if not isinstance(module_setting, ModuleSetting):
            raise TypeError(f'{setting_func}设置函数必须返回一个ModuleSetting对象')
        module_setting.name = module_name
        sub_modules = module_name.split('.')
        module_map = _modules
        for i, module in enumerate(sub_modules):
            next_module_map = module_map.get(module)
            if i == len(sub_modules) - 1:
                if next_module_map is not None:
                    raise ValueError(f'{module_name}无法被注册为设置器，因为{module_name}前缀已经被其他模块占用')
                module_map[module] = module_setting
            elif next_module_map is not None:
                module_map = next_module_map
            else:
                new_module = {}
                module_map[module] = new_module
                module_map = new_module
        return setting_func
    return wrapper

def get_settings() -> dict:
    def dfs_map(setting: dict) -> dict:
        return dict(map(lambda kv: (kv[0], kv[1].get() if isinstance(kv[1], ModuleSetting) else dfs_map(kv[1])), setting.items()))
    return dfs_map(_modules)

def update_settings(settings: dict):
    module_map = []
    def get_update_modules(setting: dict, module_dict: dict):
        for s_or_m_n, sub_setting in setting.items():
            s_or_m = module_dict.get(s_or_m_n)
            if s_or_m is not None:
                if isinstance(s_or_m, ModuleSetting):
                    try:
                        converted_setting = s_or_m.check_and_convert(sub_setting)
                    except ValueError as e:
                        raise ValueError(f'[{s_or_m.name}]{str(e)}')
                    if converted_setting is not None:
                        module_map.append((s_or_m, converted_setting))
                else:
                    get_update_modules(sub_setting, s_or_m)
    get_update_modules(settings, _modules)
    for module, converted_setting in module_map:
        module.update(converted_setting)
    for module, converted_setting in module_map:
        module.call_callback_func(converted_setting)
    config.save_config()

@init
def _subscribe_update_setting():
    from app.base.mqtt import get_mqtt_service, on_connected
    def update(settings: dict):
        try:
            if 'setting' in settings:
                update_settings(settings['setting'] if isinstance(settings['setting'], dict) else json.loads(settings['setting']))
                feedback = {
                    'ok': True,
                    'message': None
                }
            else:
                feedback = {
                    'ok': False,
                    'message': '请在setting字段中传入json格式的设置信息'
                }
        except Exception as e:
            feedback = {
                'ok': False,
                'message': str(e)
            }
        feedback['setting'] = get_settings()
        get_mqtt_service().report_update_setting_feedback(feedback)
        
    @on_connected
    def sub():
        get_mqtt_service().subscribe_update_setting(update)

    sub()