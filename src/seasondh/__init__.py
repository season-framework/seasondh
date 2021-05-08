from .interfaces import *
from .storage import *
from .base import Configuration
from .base import stdClass

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
        self.BASEPATH = os.path.join(basepath)
        self.INPUTPATH = os.path.join(self.BASEPATH, 'input')
        self.DATAPATH = os.path.join(self.BASEPATH, 'data')
        self.CACHEPATH = os.path.join(self.BASEPATH, 'cache')

        self.fs = storage.FileSystem(basepath=self.BASEPATH)
        self.package = json.loads(self.fs.read(filepath=PACKAGE_FILE, pkl=False, default=stdClass()))
        self.appsmap = dict()
        for app in self.package['apps']:
            self.appsmap[app['id']] = app

        if 'dataloader' not in self.package: raise Exception('Data Loader must be defined')
        if 'apps' not in self.package: self.package['apps'] = []

    def __getitem__(self, index):
        datafs = storage.FileSystem(basepath=self.DATAPATH)
        batch = None
        try:
            batch = datafs.read(filepath="batch_" + str(index) + '.pkl')
        except:
            pass
        if batch is None:
            batch = self.process_batch(index)
        return batch
    
    def __len__(self):
        return self.count()

    def getStorage(self, app_id='dataloader'):
        if app_id == 'dataloader':
            return storage.FileSystem(basepath=os.path.join(self.INPUTPATH, 'dataloader'))

        if app_id in self.appsmap:
            app = self.appsmap[app_id]
            return storage.FileSystem(basepath=os.path.join(self.INPUTPATH, app['id']))

        return None

    def __build_function__(self, function_str, loadclass=None):
        fn = {}
        exec(function_str, fn)
        if loadclass is not None: 
            if loadclass not in fn: return None
            return fn[loadclass]
        return fn
        
    def __process_app__(self, app, batch, **kwargs):
        appclass = self.__build_function__(app['code'], loadclass='DataProcess')
        if 'options' in app:
            for key in app['options']:
                kwargs[key] = app['options'][key]
        
        kwargs['storage'] = self.getStorage(app['id'])
        appinstance = appclass(**kwargs)
        return appinstance.process(batch)

    def getDataLoader(self, **kwargs):
        dataloaderclass = self.__build_function__(self.package['dataloader']['code'], loadclass='DataLoader')
        if 'options' in self.package['dataloader']:
            for key in self.package['dataloader']['options']:
                kwargs[key] = self.package['dataloader']['options'][key]
        kwargs['storage'] = self.getStorage()
        return dataloaderclass(**kwargs)

    def process(self, **kwargs):
        data = None
        args = dict()
        dataloader = self.getDataLoader()
        datafs = storage.FileSystem(basepath=self.DATAPATH)
        for batch_index in range(len(dataloader)):
            self.process_batch(batch_index)
    
    def process_batch(self, index, **kwargs):
        data = None
        args = dict()
        dataloader = self.getDataLoader()
        batch = dataloader[index]        
        for app in self.package['apps']:
            batch = self.__process_app__(app, batch, **kwargs)        
        if batch is not None:
            datafs = storage.FileSystem(basepath=self.DATAPATH)
            datafs.write(filepath="batch_" + str(index) + '.pkl', data=batch)
        return batch

    def process_app(self, app_index=0, batch_index=0, **kwargs):
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

        batch = self.__process_app__(app, batch, **kwargs)

        if app_index == len(self.package['apps']) - 1:
            datafs = storage.FileSystem(basepath=self.DATAPATH)
            datafs.write(filepath="batch_" + str(batch_index) + '.pkl', data=batch)
        else:
            app_id = app['id']
            cachepath = os.path.join(self.CACHEPATH, app_id)
            cachefs = storage.FileSystem(basepath=cachepath)
            cachefs.write(filepath=f'batch_{batch_index}.pkl', data=batch)

        return batch

    def clear(mode=None):
        if mode == 'cache': shutil.rmtree(self.CACHEPATH)
        if mode == 'data': shutil.rmtree(self.DATAPATH)
        if mode is None:
            shutil.rmtree(self.INPUTPATH)
            shutil.rmtree(self.CACHEPATH)
            shutil.rmtree(self.DATAPATH)
        
    def count():
        return len(self.getDataLoader())