import copy
from .util import randomstring, stdClass, Storage
from .app import app

class workflow:

    def __init__(self, **kwargs):
        kwargs = stdClass(kwargs)
        if kwargs.basepath is None: raise("`basepath` not defined")
        self.storage = storage = Storage(kwargs.basepath)
        if storage.isfile("seasondh.json") == False and kwargs.package is None:
            storage.write_json("seasondh.json", {"apps": []})

        if kwargs.use_cache is None:
            kwargs.use_cache = True

        self.config = stdClass()
        self.__basepath__ = kwargs.basepath
        self.use_cache(kwargs.use_cache)

        self.__env__ = stdClass()

        _id = self.__basepath__.split("/")
        self.__id__  = _id[-1]

        if 'package' in kwargs:
            self.__package__ = self.update(kwargs.package)
        else:
            self.__package__ = storage.read_json("seasondh.json")
            self.__build__()

    def __build__(self):
        if 'apps' not in self.__package__:
            raise Exception("Invalid package file")
        self.__instance__ = []
        prevapp = None
        for appconfig in self.__package__['apps']:
            appconfig['id'] = appconfig['__id__']
            appconfig = copy.deepcopy(appconfig)
            appconfig['prev_app'] = prevapp
            appconfig['use_cache'] = self.use_cache()
            appconfig['path'] = self.__basepath__
            _app = app(**appconfig)
            self.__instance__.append(_app)
            prevapp = _app

    def __getitem__(self, index):
        if index < self.length():
            return self.process(index)
        raise IndexError

    def __len__(self):
        return self.length()

    def get(self):
        return self.__package__

    def update(self, package):
        self.__package__ = package
        apps = self.__package__['apps']
        
        self.__env__.app_id_list = []
        for appconfig in apps:
            if '__id__' in appconfig:
                self.__env__.app_id_list.append(appconfig['__id__'])

        def genid():
            _id = randomstring(16)
            while _id in self.__env__.app_id_list:
                _id = randomstring(16)
            return _id

        for appconfig in apps:
            if '__id__' not in appconfig:
                appconfig['id'] = appconfig['__id__'] = genid()
                self.__env__.app_id_list.append(appconfig['__id__'])
            
        self.__package__['apps'] = apps
        self.storage.write_json("seasondh.json", self.__package__)

        self.__build__()
        return self.__package__

    def use_cache(self, config=None):
        if config is None:
            if self.config.use_cache == True:
                return True
            return False
        if config == True:
            self.config.use_cache = True
        else:
            self.config.use_cache = False

    def app(self, namespace):
        if type(namespace) == int:
            return self.__instance__[namespace]

        for appinstance in self.__instance__:
            if appinstance.id() == namespace:
                return appinstance
        
        raise IndexError

    def process(self, index):
        return self.__instance__[len(self.__instance__) - 1]

    def length(self):
        return len(self.__instance__)
        