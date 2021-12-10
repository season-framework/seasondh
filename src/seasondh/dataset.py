import datetime
import seasondh as sd
from seasondh.core import stage
from seasondh.core import config

class dataset:

    def __init__(self, basepath, logger=None, **kwargs):
        self.__basepath__ = basepath
        self.__kwargs__ = kwargs
        self.__logger__ = logger
        self.config = config(**kwargs)
        
        self.__data__ = None
        self.__regist__ = list()
        self.__builder__ = None

        fs = self.__storage__ = sd.util.storage(basepath)

        self.stage = stage(self)

        if fs.isfile("script.py"):
            script = fs.read("script.py")
            compiler = sd.util.compiler(seasondh=sd, dataset=self)
            if logger is not None:
                compiler.set_logger(logger)
            compiler.compile(script)

    # decorators
    # : dataset process decorators
    # - regist: regist data process
    
    def builder(self, *args, **package):
        def wrapper(func):
            def decorator(*args, **kwargs):
                return func(*args, **kwargs)

            package['process'] = decorator
            self.__builder__ = package
            return decorator

        if len(args) > 0:
            func = args[0]
            return wrapper(func)

        return wrapper

    def regist(self, *args, **package):                
        def wrapper(func):
            def decorator(*args, **kwargs):
                return func(*args, **kwargs)

            namespace = package['namespace']

            if namespace == "build":
                raise Exception("seasondh: deny using namespace `build`")

            package['process'] = decorator

            namespaces = self.stage.namespaces()
            if namespace in namespaces:
                find = namespaces.index(namespace)
                self.__regist__[find] = package
            else:
                self.__regist__.append(package)
            return decorator

        if len(args) > 0:
            func = args[0]
            if 'namespace' not in package:
                package['namespace'] = func.__name__
            return wrapper(func)

        if 'namespace' not in package:
            raise Exception("seasondh: not defined namespace")

        return wrapper

    # list magic functions
    # : dataset as list
    def __setitem__(self, index, value):
        pass
        
    def __getitem__(self, index):
        return

    def __delitem__(self, index):
        pass

    def __iter__(self):
        pass

    def __next__(self):
        if self.__position__ >= len(self):
            raise StopIteration
        
        data = self.__getitem__(self.__position__)
        self.__position__ += 1
        return data

    def __len__(self):
        return len(self.__indexes__)

    def process(self):
        pass

    # general functions
    # : dataset functions
    # - use: change namespace of dataset
    # - update: save changed of dataset from cached

    # def build(self):
    #     if self.__builder__ is not None:
    #         self.__builder__['process']()

    # def process(self, mode="bulk"):
    #     regists = self.__regist__
    #     if len(regists) == 0:
    #         return

    #     self.build()

    #     if mode == "online":
    #         fs = self.__storage__.use("dataset").cd(self.namespace)

    #         try: online_pos = fs.read.pickle("__online__")
    #         except: online_pos = -1

    #         for position in range(len(self)):
    #             if position <= online_pos:
    #                 continue

    #             self.__position__ = position
    #             for stage in regists:
    #                 func = stage['process']
    #                 self.data(func())

    #             self.update()
    #             fs.write.pickle("__online__", position)
        
    #     else:
    #         for stage in regists:
    #             for position in range(len(self)):
    #                 self.__position__ = position
    #                 func = stage['process']
    #                 self.data(func())
    #         self.update()

    # def data(self):
    #     if namespace is None:
    #         namespace = self.namespace
        
    #     if data is None:
    #         return self[self.__position__]
    #     self[self.__position__] = data

    def clear(self):
        fs = self.__storage__.use("dataset")
        fs = self.__storage__.use("stage")
        fs.remove()

    def storage(self):
        return self.__storage__.use("storage")
