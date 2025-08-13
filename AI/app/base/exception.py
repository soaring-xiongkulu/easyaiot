class AIManagerError(RuntimeError):
    def __init__(self, code, msg):
        super().__init__(msg)
        self.code = code
        self.msg = msg

class SystemInternalError(AIManagerError):
    def __init__(self, msg):
        super().__init__(-1, msg)