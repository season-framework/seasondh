import time
_compile = compile
_print = print

class compiler:
    def __init__(self, **kwargs):
        self.kwargs = kwargs
        self.logger = _print

    def set_logger(self, logger):
        self.logger = logger

    def set(self, **kwargs):
        for key in kwargs:
            self.kwargs[key] = kwargs[key]
        
    def compile(self, code):
        kwargs = self.kwargs
        logger = self.logger
        obj = globals()
        obj['print'] = logger

        for key in kwargs: obj[key] = kwargs[key]
        exec(_compile(code, __name__, 'exec'), obj)

        return obj
