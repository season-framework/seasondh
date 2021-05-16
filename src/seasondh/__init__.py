from .interfaces import *
from .storage import *
from .base import Configuration
from .base import stdClass

import gc
import zipfile
import os
import shutil
import json

PACKAGE_FILE = 'seasondh.json'

def parse_json(jsonstr, default=None):
    try:
        return json.loads(jsonstr)
    except:
        return default

class dataset:
    def __init__(self, basepath, **kwargs):
        self.config = Configuration(**kwargs)
        self.kwargs = kwargs
        self.BASEPATH = os.path.join(basepath)
        self.INPUTPATH = os.path.join(self.BASEPATH, 'input')
        self.DATAPATH = os.path.join(self.BASEPATH, 'data')
        self.CACHEPATH = os.path.join(self.BASEPATH, 'cache')

        self.fs = storage.FileSystem(basepath=self.BASEPATH)
        self.package = json.loads(self.fs.read(filepath=PACKAGE_FILE, pkl=False, default=stdClass()))
        
        if 'dataloader' not in self.package: raise Exception('Data Loader must be defined')
        if 'apps' not in self.package: self.package['apps'] = []

        self.appsmap = dict()
        for app in self.package['apps']:
            self.appsmap[app['id']] = app

    def __walkdir__(self, dirname, mode='all'):
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

    def __getitem__(self, index):
        use_cache = False
        forced = False
        if 'use_cache' in self.kwargs: use_cache = self.kwargs['use_cache']
        if 'forced' in self.kwargs: forced = self.kwargs['forced']
        
        datafs = storage.FileSystem(basepath=self.DATAPATH)
        batch = None
        if use_cache:
            try:
                batch = datafs.read(filepath="batch_" + str(index) + '.pkl')
            except:
                pass
        if batch is None:
            batch = self.process_batch(index, **self.kwargs)
        return batch
    
    def __len__(self):
        try:
            return self.count()
        except:
            pass

        lastfname = ""
        for root, dirs, files in os.walk(self.DATAPATH):
            for filename in files:
                lastfname = filename
        return int(lastfname.split('_')[1].split('.')[0])

    def __build_function__(self, function_str, loadclass=None):
        fn = {}
        exec(function_str, fn)
        if loadclass is not None: 
            if loadclass not in fn: return None
            return fn[loadclass]
        return fn
        
    # get Storage
    def getStorage(self, **kwargs):
        return self.get_storage(**kwargs)

    def get_storage(self, app_id='dataloader'):
        if app_id == 'dataloader':
            return storage.FileSystem(basepath=os.path.join(self.INPUTPATH, 'dataloader'))

        if app_id in self.appsmap:
            app = self.appsmap[app_id]
            return storage.FileSystem(basepath=os.path.join(self.INPUTPATH, app['id']))

        return None

    # get dataloader
    def getDataLoader(self, **kwargs):
        return self.get_dataloader(**kwargs)

    def get_dataloader(self, **kwargs):
        dataloaderclass = self.__build_function__(self.package['dataloader']['code'], loadclass='DataLoader')
        for key in self.kwargs:
            kwargs[key] = self.kwargs[key]
        kwargs['storage'] = self.getStorage()
        return dataloaderclass(**kwargs)

    #get previous batch 
    def getPreviousBatch(self, **kwargs):
        return self.get_previous_batch(**kwargs)

    def get_previous_batch(self, app_id=None, batch_index=0, **kwargs):
        if app_id is None: raise Exception('Out of Index: Apps')

        app_index = 0
        for app in self.package['apps']:
            if app['id'] == app_id:
                break
            app_index = app_index + 1

        if app_index == 0: 
            dataloader = self.getDataLoader()
            batch = dataloader[batch_index]
        else:
            prevapp = self.package['apps'][app_index - 1]
            prevapp_id = prevapp['id']
            prevcachepath = os.path.join(self.CACHEPATH, prevapp_id)
            prevcachefs = storage.FileSystem(basepath=prevcachepath)
            batch = prevcachefs.read(filepath=f'batch_{batch_index}.pkl')

        return batch

    # process all
    def process(self, **kwargs):
        args = dict()
        dataloader = self.getDataLoader()
        for batch_index in range(len(dataloader)):
            self.process_batch(batch_index, **kwargs)
    
    # process for batch
    def processBatch(self, index, **kwargs):
        return self.process_batch(index, **kwargs)

    def process_batch(self, index, **kwargs):
        args = dict()
        batch = None
        
        if len(self.package['apps']) == 0:
            dataloader = self.getDataLoader()
            batch = dataloader[index]

        for app in self.package['apps']:
            batch = self.process_app(app_id=app['id'], batch_index=index, **kwargs)
            if batch is None:
                kwargs['use_cache'] = False
                batch = self.process_app(app_id=app['id'], batch_index=index, **kwargs)
                
        if batch is not None:
            datafs = storage.FileSystem(basepath=self.DATAPATH)
            datafs.write(filepath="batch_" + str(index) + '.pkl', data=batch)
        return batch

    # process for single app
    def processApp(self, **kwargs):
        return self.process_app(**kwargs)

    def process_app(self, app_id=None, batch_index=0, use_cache=True, forced=False, **kwargs):
        if app_id is None: raise Exception('Out of Index: Apps')

        app_index = 0
        for app in self.package['apps']:
            if app['id'] == app_id:
                break
            app_index = app_index + 1

        if use_cache and forced is False:
            app_id = app['id']
            cachepath = os.path.join(self.CACHEPATH, app_id)
            cachefs = storage.FileSystem(basepath=cachepath)
            cache = cachefs.read(filepath=f'batch_{batch_index}.pkl')
            if cache is not None:
                return cache

        dataloader = self.getDataLoader()
        if len(dataloader) <= batch_index: raise Exception('Out of Index: DataLoader')
        if len(self.package['apps']) <= app_index: raise Exception('Out of Index: Apps')
        
        if app_index == 0: 
            batch = dataloader[batch_index]
        else:
            prevapp = self.package['apps'][app_index - 1]
            prevapp_id = prevapp['id']
            prevcachepath = os.path.join(self.CACHEPATH, prevapp_id)
            prevcachefs = storage.FileSystem(basepath=prevcachepath)
            batch = prevcachefs.read(filepath=f'batch_{batch_index}.pkl')
            
        if batch is None: raise Exception('Process Error: Cache not found for previous app.')

        app = self.package['apps'][app_index]

        kwargs['index'] = batch_index
        res_batch = self.__process_app__(app, batch, **kwargs)
        
        app_id = app['id']
        cachepath = os.path.join(self.CACHEPATH, app_id)
        cachefs = storage.FileSystem(basepath=cachepath)
        cachefs.write(filepath=f'batch_{batch_index}.pkl', data=res_batch)

        return batch

    # process basic fn 
    def __process_app__(self, app, batch, **kwargs):
        appclass = self.__build_function__(app['code'], loadclass='DataProcess')
        if 'options' in app:
            for key in app['options']:
                kwargs[key] = app['options'][key]
        
        kwargs['storage'] = self.getStorage(app_id=app['id'])
        appinstance = appclass(**kwargs)
        return appinstance.__process__(batch, **kwargs)


    # find app
    def findApp(self, app_id):
        return self.find_app(app_id) 

    def find_app(self, app_id):
        if self.package['dataloader']['id'] == app_id:
            return self.package['dataloader']
        for app in self.package['apps']:
            if app['id'] == app_id:
                return app
        return None

    # dataset clear
    def clear(self, mode=None):
        if mode == 'cache': shutil.rmtree(self.CACHEPATH)
        if mode == 'data': shutil.rmtree(self.DATAPATH)
        if mode == 'input': shutil.rmtree(self.INPUTPATH)
        if mode is None:
            shutil.rmtree(self.CACHEPATH)
            shutil.rmtree(self.DATAPATH)
        
    def count(self):
        return len(self.getDataLoader())

    def zip(self, FILEPATH, mode=None):
        DATASET_PATH = self.BASEPATH
        targets = self.__walkdir__(DATASET_PATH, mode=mode)
        dataset_zip = zipfile.ZipFile(FILEPATH, 'w')
        for target in targets:
            abspath, relpath = target
            dataset_zip.write(abspath, relpath, compress_type=zipfile.ZIP_DEFLATED)
        dataset_zip.close()
        return FILEPATH