class BaseDriver:
    def __init__(self, config):
        self.config = config

    async def connect(self):
        raise NotImplementedError

    async def read_data(self):
        raise NotImplementedError

    async def disconnect(self):
        raise NotImplementedError
