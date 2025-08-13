from app.base.exception import AIManagerError

class TrainingError(AIManagerError):
    def __init__(self, msg):
        super().__init__(10000, msg)

class ModelNotFoundError(AIManagerError):
    def __init__(self, msg):
        super().__init__(10001, msg)

class ExportError(AIManagerError):
    def __init__(self, msg):
        super().__init__(10002, msg)

class InvalidDatasetError(AIManagerError):
    def __init__(self, msg):
        super().__init__(10003, msg)

class DatasetDownloadError(AIManagerError):
    def __init__(self, msg):
        super().__init__(10004, msg)
