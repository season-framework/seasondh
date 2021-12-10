import datetime
import seasondh as sd
import inspect

class config:
    def __init__(self, **kwargs):
        self.data = sd.util.stdClass(**kwargs)
        
        self.defaults = sd.util.stdClass()
        self.defaults.cache = "memory"

    def __getattr__(self, key):
        def fn(value=None):
            if value is None:
                value = self.data[key]
                if value is None:
                    value = self.defaults[key]
                return value

            self.data[key] = value
            return self.data[key]
        return fn

class stage:
    def __init__(self, _dataset):
        self.__dataset__ = _dataset
        self.__storage__ = _dataset.__storage__
        self.dataset_namespace = _dataset.namespace
        self.namespace = None

        namespaces = []
        for pkg in _dataset.__stage__: namespaces.append(pkg['namespace'])
        self.__stages__ = namespaces
        
        self.__position__ = 0
        self.__current__ = self.get(0)

    def __getitem__(self, index):
        return self.get(index)

    def __iter__(self):
        self.__position__ = 0
        return self

    def __next__(self):
        if self.__position__ >= len(self):
            raise StopIteration
        stage = self.__getitem__(self.__position__)
        self.__position__ += 1
        return stage

    def __len__(self):
        return len(self.__stages__)

    def get(self, index):
        if type(index) == str:
            if index in self.__stages__:
                index = self.__stages__.index(index)
            else:
                raise ValueError

        self.__current__ = self.__dataset__.__stage__[index]
        self.namespace = self.__current__['namespace']
        return self
    
    def process(self, index=-1):
        fs = self.__storage__.use("stage").cd(self.namespace).cd(self.dataset_namespace)

        func = self.__current__['process']
        if index > -1:
            self.__dataset__.__position__ = index
            data = func()
            fs.write.pickle(str(index), data)
            return

        for position in range(len(self.__dataset__)):
            self.__dataset__.__position__ = position
            data = func()

class dataset:

    def __init__(self, basepath, namespace="default", logger=None, **kwargs):
        self.__basepath__ = basepath
        self.__kwargs__ = kwargs
        self.__logger__ = logger
        self.namespace = namespace
        self.config = config(**kwargs)
        self.__stage__ = list()
        self.__builder__ = None

        fs = self.__storage__ = sd.util.storage(basepath)

        # inmemory data
        self.__data__ = sd.util.stdClass()
        self.__data__.deleted = dict()
        self.__data__.updated = dict()
        self.__data__.cached = dict()
        if self.namespace not in self.__data__.updated: self.__data__.updated[self.namespace] = dict()
        if self.namespace not in self.__data__.cached: self.__data__.cached[self.namespace] = dict()
        if self.namespace not in self.__data__.deleted: self.__data__.deleted[self.namespace] = dict()

        # load indexes
        self.__initindex__()

        if fs.isfile("script.py"):
            script = fs.read("script.py")
            compiler = sd.util.compiler(sd=sd, dataset=self)
            if logger is not None:
                compiler.set_logger(logger)
            compiler.compile(script)

        # iter variables
        self.__position__ = 0
        self.stage = stage(self)

    # decorators
    # : dataset process decorators
    # - regist: regist data process
    
    def builder(self, **package):
        def wrapper(func):
            def decorator(*args, **kwargs):
                return func(*args, **kwargs)

            package['process'] = decorator
            self.__builder__ = package
            return decorator
        return wrapper

    def regist(self, **package):
        namespace = self.namespace
        if 'namespace' in package: namespace = package['namespace']

        def wrapper(func):
            def decorator(*args, **kwargs):
                return func(*args, **kwargs)
            package['namespace'] = namespace
            package['process'] = decorator

            namespaces = []
            for pkg in self.__stage__:
                namespaces.append(pkg['namespace'])

            if namespace in namespaces:
                find = namespaces.index(namespace)
                self.__stage__[find] = package
            else:
                self.__stage__.append(package)
            return decorator
        return wrapper

    # private functions
    # : internal functions

    def __initindex__(self):
        try:
            self.__indexes__ = None
            if self.config.cache() != "memory":
                fs = self.__storage__.use("cache").cd(self.namespace)
                if fs.isfile("__indexes__"): 
                    self.__indexes__ = fs.read.pickle("__indexes__")
            
            if self.__indexes__ is None:
                fs = self.__storage__.use("dataset").cd(self.namespace)
                if fs.isfile("__indexes__"): 
                    self.__indexes__ = fs.read.pickle("__indexes__")

            if self.__indexes__ is None: 
                self.__indexes__ = list()
        except:
            self.clear()
            self.__indexes__ = list()

    def __update__(self, key, value):
        if key in self.__data__.deleted[self.namespace]: 
            del self.__data__.deleted[self.namespace][key]

        if self.config.cache() == "memory":
            self.__data__.updated[self.namespace][key] = value
        else:
            fs = self.__storage__.use("cache").cd(self.namespace)
            fs.write.pickle(str(key), value)

    # list magic functions
    # : dataset as list

    def __setitem__(self, index, value):
        if index < 0:
            raise ValueError
        index = self.__indexes__[index]
        self.__update__(index, value)
        
    def __getitem__(self, index):
        key = self.__indexes__[index]

        if type(key) == list:
            obj = dataset(self.__basepath__, namespace=self.namespace, logger=self.__logger__, **self.__kwargs__)
            obj.__indexes__ = list()
            for idx in key:
                obj.append(self.__getitem__(idx))
            return obj

        if self.config.cache() == "memory":
            if key in self.__data__.updated[self.namespace]:
                return self.__data__.updated[self.namespace][key]
            if key in self.__data__.cached[self.namespace]:
                return self.__data__.cached[self.namespace][key]
        else:
            cachefs = self.__storage__.use("cache").cd(self.namespace)
            try:
                if cachefs.isfile(str(key)):
                    return cachefs.read.pickle(str(key))
            except:
                pass
        
        fs = self.__storage__.use("dataset").cd(self.namespace)
        if fs.isfile(str(key)) == False:
            raise ValueError
        data = fs.read.pickle(str(key))

        if self.config.cache() == "memory":
            self.__data__.cached[self.namespace][key] = data
        
        return data

    def __delitem__(self, index):
        key = self.__indexes__[index]
        
        if self.config.cache() == "memory":
            if key in self.__data__.updated[self.namespace]: del self.__data__.updated[self.namespace][key]
            if key in self.__data__.cached[self.namespace]: del self.__data__.cached[self.namespace][key]
        else:
            cachefs = self.__storage__.use("cache").cd(self.namespace)
            try:
                cachefs.remove(str(key))
            except:
                pass
        
        self.__data__.deleted[self.namespace][key] = True
        
        del self.__indexes__[index]

    def __iter__(self):
        self.__position__ = 0
        return self

    def __next__(self):
        if self.__position__ >= len(self):
            raise StopIteration
        
        data = self.__getitem__(self.__position__)
        self.__position__ += 1
        return data

    def __len__(self):
        return len(self.__indexes__)

    # general functions
    # : dataset functions
    # - use: change namespace of dataset
    # - update: save changed of dataset from cached

    def use(self, namespace, inplace=True):
        if inplace:
            self.namespace = namespace
            if self.namespace not in self.__data__.updated: self.__data__.updated[self.namespace] = dict()
            if self.namespace not in self.__data__.cached: self.__data__.cached[self.namespace] = dict()
            if self.namespace not in self.__data__.deleted: self.__data__.deleted[self.namespace] = dict()
            
            self.__initindex__()
            return self

        dataset = Dataset(self.__basepath__, namespace=namespace, **self.__kwargs__)
        return dataset

    def build(self):
        if self.__builder__ is not None:
            self.__builder__['process']()

    def process(self, mode="bulk"):
        stages = self.__stage__
        if len(stages) == 0:
            return

        self.build()

        if mode == "online":
            fs = self.__storage__.use("dataset").cd(self.namespace)

            try: online_pos = fs.read.pickle("__online__")
            except: online_pos = -1

            for position in range(len(self)):
                if position <= online_pos:
                    continue

                self.__position__ = position
                for stage in stages:
                    func = stage['process']
                    self.data(func())

                self.update()
                fs.write.pickle("__online__", position)
        
        else:
            for stage in stages:
                for position in range(len(self)):
                    self.__position__ = position
                    func = stage['process']
                    self.data(func())
            self.update()

    def position(self, position=None):
        if position is None:
            return self.__position__
        self.__position__ = int(position)

    def data(self, data=None):
        if data is None:
            return self[self.__position__]
        self[self.__position__] = data

    def update(self):
        fs = self.__storage__.use("dataset").cd(self.namespace)

        # update dataset from memory
        if self.config.cache() == "memory":
            data = self.__data__.updated[self.namespace]
            for key in data:
                fs.write.pickle(str(key), data[key])
            
            self.__data__.updated[self.namespace] = dict()
        
        # update dataset from cache folder
        else:
            try:
                cachefs = self.__storage__.use("cache").cd(self.namespace)
                fs.copy(cachefs.abspath(), ".")
                cachefs.delete()
            except:
                pass

        # delete data
        data = self.__data__.deleted[self.namespace]
        for key in data:
            try:
                fs.delete(str(key))
            except:
                pass
        self.__data__.deleted[self.namespace] = dict()

        fs.write.pickle("__indexes__", self.__indexes__)

    def clear(self, namespace=None):
        if namespace is None:
            namespace = self.namespace

        fs = self.__storage__.use("dataset")
        cachefs = self.__storage__.use("cache")

        if namespace is not True:
            fs.cd(namespace)
            cachefs.cd(namespace)
        
        fs.remove()
        cachefs.remove()

        self.__indexes__ = list()

    def push(self, *args):
        self.append(**args)

    def append(self, *args):
        for arg in args:
            if len(self.__indexes__) == 0: index = 0
            else: index = self.__indexes__[-1] + 1
            self.__update__(index, arg)
            self.__indexes__.append(index)

        if self.config.cache() != "memory":
            cachefs = self.__storage__.use("cache").cd(self.namespace)
            cachefs.write.pickle("__indexes__", self.__indexes__)

    def remove(self, index):
        self.__delitem__(index)
        
    def last(self):
        return self.__indexes__[-1]

    def tolist(self):
        res = []
        for i in range(len(self)):
            res.append(self[i])
        return res

    def namespaces(self):
        fs = self.__storage__.use("dataset")
        namespaces = fs.ls()
        res = []
        for ns in namespaces:
            if ns[0] == ".": continue
            if ns[0] == "_": continue
            res.append(ns)
        return namespaces

    def storage(self):
        return self.__storage__.use("storage")
