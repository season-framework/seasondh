import datetime
import seasondh as sd
from seasondh.core import stage
from seasondh.core import config
from seasondh.core import data as sddata

class dataset:

    def __init__(self, basepath, logger=None, **kwargs):
        self.__basepath__ = basepath
        self.__kwargs__ = kwargs
        self.__logger__ = logger
        self.config = config(**kwargs)
        
        fs = self.__storage__ = sd.util.storage(basepath)

        self.init()

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
    
    def __getitem__(self, index):
        return self.get(index)

    def __iter__(self):
        pass

    def __next__(self):
        if self.__position__ >= len(self):
            raise StopIteration
        
        data = self.__getitem__(self.__position__)
        self.__position__ += 1
        return data

    def __len__(self):
        if self.readonly:
            fs = self.__storage__.use("dataset")
            data = sddata(fs)
            if data.exists():
                return len(data)
            return 0

        last_stage = self.stage.last()
        return len(last_stage.data)

    # general functions
    # : dataset functions
    # - use: change namespace of dataset
    # - update: save changed of dataset from cached

    def get(self, index):        
        # if stage data not exists in dataset dir
        if self.readonly:
            fs = self.__storage__.use("dataset")
            data = sddata(fs)
            if data.exists():
                try:        
                    item = data[index]
                except Exception as e:
                    item = type(e)

                if item not in [IndexError, ValueError]:
                    return item

            raise item

        last_stage = self.stage.last()
        err = None

        try:
            item = last_stage.data[index]
        except Exception as e:
            err = e
            item = type(e)

        if item in [IndexError, ValueError]:
            self.stage.build()
            for stage in self.stage:
                stage(index)
            item = last_stage.data[index]
            self.stage.save()
        elif err is not None:
            raise err

        if item is ValueError:
            raise ValueError

        return item

    def process(self):
        fs = self.__storage__.use("dataset")
        fs.delete()

        build_data = self.stage.data.build()
        
        data = sddata(fs)
        data.set(build_data)

        for index in range(len(build_data)):
            err = None
            try:
                item = self[index]
            except Exception as e:
                err = e
                item = type(e)
            
            if item in [IndexError, ValueError]:
                for stage in self.stage:
                    stage(index)
            elif err is not None:
                raise err

            last_stage = self.stage.last()
            item = last_stage.data[index]
            data[index] = item
        
        self.stage.save()
        data.save()

    def logger(self, *args):
        logger = self.__logger__
        if logger is not None:
            logger(*args)

    def init(self):
        logger = self.__logger__

        self.stage = stage(self)
        self.__regist__ = list()
        self.__builder__ = None
        
        script = self.script()

        compiler = sd.util.compiler(seasondh=sd, dataset=self)
        if logger is not None:
            compiler.set_logger(logger)
        compiler.compile(script)

        self.readonly = False
        if len(self.stage) == 0 or self.stage.last().data().exists() == False:
            self.readonly = True

    def script(self, script=None):
        fs = self.__storage__
        if script is None:
            return fs.read("script.py", "")
        
        fs.write("script.py", script)
        self.init()
        return script

    def clear(self):
        fs = self.__storage__.use("dataset")
        fs = self.__storage__.use("stage")
        fs.remove()

    def storage(self):
        return self.__storage__.use("storage")
