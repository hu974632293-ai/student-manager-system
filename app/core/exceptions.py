class ServiceError(Exception):
    def __init__(self, msg: str, data=None):
        super().__init__(msg)
        self.msg = msg
        self.data = data
