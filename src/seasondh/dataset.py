from .interfaces import *
from .storage import *
from .base import stdClass
from .version import VERSION_STRING

import gc
import zipfile
import os
import shutil
import json

__PACKAGEFILENAME__ = 'seasondh.json'

version = VERSION_STRING

# utils
class __util__:

    def print(*args):
        print(*args)

    def parse_json(self, jsonstr, default=None):
        try:
            return json.loads(jsonstr)
        except:
            return default

    def walkdir(self, dirname, mode='all'):
        result = []
        for root, dirs, files in os.walk(dirname):
            for filename in files:
                if filename.startswith('.'): continue
                abspath = os.path.join(root, filename)
                relpath = os.path.relpath(abspath, dirname)

                if mode == 'all':
                    result.append((abspath, relpath))
                elif mode == 'data':
                    if relpath.startswith('cache/') == False and relpath.startswith('input/') == False:
                        result.append((abspath, relpath))

        return result

    def build_function(self, function_str, loadclass=None):
        fn = {}
        exec(function_str, fn)

        fn['print'] = self.print
        if loadclass is not None: 
            if loadclass not in fn: return None
            return fn[loadclass]
        return fn

__util__ = __util__()

# dataset definition
class dataset:

    __defaultoptions__ = {
        "cache": True
    }

    def setPrint(self, printfn):
        self.set_print(printfn)

    def set_print(self, printfn):
        __util__.print = printfn

    def option(self, key):
        if key in self.__kwargs__:
            return self.__kwargs__[key]
        if key in self.__defaultoptions__:
            return self.__defaultoptions__[key]
        return None

    # set options
    def setOption(self, **kwargs):
        return self.set_option(**kwargs)

    def set_option(self, **kwargs):
        for key in kwargs:
            self.__kwargs__[key] = kwargs[key]
        return self

    # init class instance
    def __init__(self, basepath, **kwargs):
        self.__kwargs__ = kwargs

        self.BASEPATH = os.path.join(basepath)
        self.INPUTPATH = os.path.join(self.BASEPATH, 'input')
        self.DATAPATH = os.path.join(self.BASEPATH, 'data')
        self.CACHEPATH = os.path.join(self.BASEPATH, 'cache')

        basefs = FileSystem(self.BASEPATH)
        self.package = json.loads(basefs.read(__PACKAGEFILENAME__))
        
        if 'dataloader' not in self.package: raise Exception('Data Loader must be defined')
        if 'apps' not in self.package: self.package['apps'] = []

        self.__appsmap__ = dict()
        for app in self.package['apps']:
            self.__appsmap__[app['id']] = app
    
    # get Apps
    def getApps(self):
        return self.get_apps()

    def get_apps(self):
        apps = self.package['apps']
        result = []
        for app in apps:
            result.append(app['id'])
        return result

    # get app
    def getApp(self, app_id):
        return self.get_app(app_id) 

    def get_app(self, app_id):
        if self.package['dataloader']['id'] == app_id:
            return self.package['dataloader']
        for app in self.package['apps']:
            if app['id'] == app_id:
                return app
        return None

    # input storage api
    def getStorage(self, app_id="dataloader"):
        return self.get_storage(app_id)

    def get_storage(self, app_id="dataloader"):
        if app_id == 'dataloader':
            return FileSystem(os.path.join(self.INPUTPATH, 'dataloader'))
        if app_id in self.__appsmap__:
            app = self.__appsmap__[app_id]
            return FileSystem(os.path.join(self.INPUTPATH, app['id']))
        return None

    # data loader api
    def getDataLoader(self):
        return self.get_dataloader()

    def getDataloader(self):
        return self.get_dataloader()

    def get_dataloader(self):
        kwargs = dict()
        kwargs['dataset'] = self
        kwargs['storage'] = self.getStorage()
        dataloaderclass = __util__.build_function(self.package['dataloader']['code'], loadclass='DataLoader')
        return dataloaderclass(**kwargs)

    #get previous batch 
    def getPreviousBatch(self, **kwargs):
        return self.get_previous_batch(**kwargs)

    def get_previous_batch(self, app_id=None, batch_index=0):
        if app_id is None: raise Exception('Out of Index: Apps')
        cache = self.option('cache')
        dataloader = self.getDataLoader()

        app_index = 0
        for app in self.package['apps']:
            if app['id'] == app_id:
                break
            app_index = app_index + 1

        app_index = app_index - 1

        if app_index < 0:
            if cache:
                CACHEPATH = os.path.join(self.CACHEPATH, 'dataloader')
                batchfs = FileSystem(CACHEPATH)
                try:
                    batch = batchfs.read_pickle(f'batch_{batch_index}.pkl')
                except:
                    batch = None

                if batch is not None:
                    return batch

            return dataloader[batch_index]
        else:
            app_id = self.package['apps'][app_index]['id']

        return self.run(app_id=app_id, batch_index=batch_index)

    # process api
    def run(self, app_id=None, batch_index=0):
        cache = self.option('cache')
        dataloader = self.getDataLoader()
        batch = None

        APP_COUNT = len(self.package['apps'])
        CACHEPATH = None

        # check batch index
        if len(dataloader) <= batch_index: 
            raise Exception('Out of Index: DataLoader')

        if APP_COUNT == 0:
            if cache:
                CACHEPATH = os.path.join(self.CACHEPATH, 'dataloader')
                batchfs = FileSystem(CACHEPATH)
                try:
                    batch = batchfs.read_pickle(f'batch_{batch_index}.pkl')
                except:
                    batch = None
                if batch is not None:
                    return batch
            return dataloader[batch_index]

        # find app index
        app_index = 0
        if app_id is None: 
            app_index = APP_COUNT - 1
            app_id = self.package['apps'][app_index]['id']
        else:
            for app in self.package['apps']:
                if app['id'] == app_id:
                    break
                app_index = app_index + 1

        if app_index < 0 or app_index >= APP_COUNT:
            raise Exception('Out of Index: Apps')

        # set cache path
        if app_index >= APP_COUNT - 1:
            CACHEPATH = self.DATAPATH
        else:
            CACHEPATH = os.path.join(self.CACHEPATH, app_id)

        # return cache data, if use cache
        if cache:
            cachefs = FileSystem(CACHEPATH)
            try:
                batch = cachefs.read_pickle(f'batch_{batch_index}.pkl')
            except:
                batch = None
            if batch is not None:
                return batch
        
        # find previous app
        prevapp_id = None
        if app_index > 0:
            prevapp = self.package['apps'][app_index - 1]
            prevapp_id = prevapp['id']
        elif app_index == 0:
            prevapp_id = 'dataloader'
        else:
            raise Exception('Out of Index: Apps')

        # load previous batch, if use cache
        if cache:
            previousbatchpath = os.path.join(self.CACHEPATH, prevapp_id)
            previousbatchfs = FileSystem(previousbatchpath)
            try:
                batch = previousbatchfs.read_pickle(f'batch_{batch_index}.pkl')
            except:
                batch = None

        # load batch, if batch is none
        if batch is None:
            if app_index == 0:
                batch = dataloader[batch_index]
            else:
                batch = self.run(app_id=prevapp_id, batch_index=batch_index)

        if batch is None:
            raise Exception('Process Error: unable build batch')

        app = self.package['apps'][app_index]

        appclass = __util__.build_function(app['code'], loadclass='DataProcess')
        appopts = dict()
        appopts['index'] = batch_index
        appopts['dataset'] = self
        appopts['storage'] = self.getStorage(app_id)
        appinstance = appclass(**appopts)

        batch = appinstance.__process__(batch, **appopts)

        # if cache save mode
        if cache and batch is not None:
            cachefs = FileSystem(CACHEPATH)
            cachefs.write_pickle(f'batch_{batch_index}.pkl', batch)

        return batch

    # dataset clear
    def clear(self, mode='cache'):
        try:
            if mode == 'cache': 
                shutil.rmtree(self.CACHEPATH)
                shutil.rmtree(self.DATAPATH)
            if mode == 'storage': 
                shutil.rmtree(self.INPUTPATH)
        except:
            pass
        return self

    # create zip file
    def zip(self, FILEPATH, mode=None):
        DATASET_PATH = self.BASEPATH
        targets = __util__.walkdir(DATASET_PATH, mode=mode)
        dataset_zip = zipfile.ZipFile(FILEPATH, 'w')
        for target in targets:
            abspath, relpath = target
            dataset_zip.write(abspath, relpath, compress_type=zipfile.ZIP_DEFLATED)
        dataset_zip.close()
        return FILEPATH

    # array api
    def __getitem__(self, index):
        return self.run(batch_index=index)

    def __len__(self):
        try:
            return len(self.getDataLoader())
        except:
            pass

        lastfname = ""
        maxsize = 0
        for root, dirs, files in os.walk(self.DATAPATH):
            for filename in files:
                lastfname = filename
                s = int(lastfname.split('_')[1].split('.')[0]) + 1
                if s > maxsize:
                    maxsize = s
        return maxsize