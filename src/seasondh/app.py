from .util import stdClass, Storage
from .spawner import Spawner
import json
import copy
import os
import lesscpy
from six import StringIO
import pypugjs

SEASONDH_JS = """
if(!window.season_datahub) {
    window.season_datahub = function(api_base_url, workflow_id, app_id) {
        var fn = function (url, data, cb, opts) {
            var ajax = {
                url: url,
                type: 'POST',
                data: data
            };

            if (opts) {
                for (var key in opts) {
                    ajax[key] = opts[key];
                }
            }

            $.ajax(ajax).always(function (a, b, c) {
                if (cb) cb(a, b, c);
            });
        }

        var seasondh = {};
        seasondh.API = {};
        seasondh.API.url = function(fnname) {
            return api_base_url + '/' + workflow_id + '/' + app_id + '/' + fnname;
        }
        seasondh.API.function = function(fnname, data, cb, opts) {
            var _url = seasondh.API.url(fnname);
            fn(_url, data, cb, opts)
        }

        return seasondh;
    }
}
"""

class app:
    def __init__(self, **kwargs):
        self.__kwargs__ = kwargs
        kwargs = stdClass(kwargs)
        if '__id__' not in kwargs: raise Exception("`__id__` not in config")
        if 'path' not in kwargs: raise Exception("`path` not in config")
        if 'batch_api' not in kwargs: raise Exception("`batch_api` not in config")

        if kwargs.use_cache is None:
            kwargs.use_cache = True

        self.prev_app = kwargs.prev_app

        self.__id__ = kwargs.__id__
        _id = kwargs.path.split("/")
        self.__workflowid__ = _id[-1]

        self.config = stdClass()
        self.use_cache(kwargs.use_cache)
        self.config.path = os.path.join(kwargs.path, self.__id__)

        self.cache = storage_cache(self.config.path)
        
        self.__view__ = stdClass()
        self.__view__.html = kwargs.html
        self.__view__.js = kwargs.js
        self.__view__.css = kwargs.css

        self.api = stdClass()
        self.api.batch = self.__pybuilder__(kwargs.batch_api)
        self.api.view = None
        if 'view_api' in kwargs: self.api.view = self.__pybuilder__(kwargs.view_api)
        
    def __pybuilder__(self, code, instance=None):
        try:
            fn = {'__file__': 'seasondh.app', '__name__': 'seasondh.app'}
            fn = stdClass(fn)
            exec(compile(code, 'seasondh.app', 'exec'), fn)
        except Exception as e:
            return stdClass()
        return fn

    def __getitem__(self, index):
        if index < self.length():
            return self.process(index)
        raise IndexError

    def __len__(self):
        return self.length()

    def to_dict(self):
        appconfig = self.__kwargs__
        if 'prev_app' in appconfig: del appconfig['prev_app']
        if 'use_cache' in appconfig: del appconfig['use_cache']
        if 'path' in appconfig: del appconfig['path']
        return appconfig

    def json(self):
        appconfig = self.to_dict()
        return json.dumps(appconfig, indent=4, sort_keys=True)
    
    def id(self):
        return self.__id__
    
    def instance(self):
        return app_instance(self)

    def path(self):
        return self.config.path

    def use_cache(self, config=None):
        if config is None:
            if self.config.use_cache == True:
                return True
            return False
        if config == True:
            self.config.use_cache = True
        else:
            self.config.use_cache = False

    def clear(self):
        self.cache.clear()

    def length(self):
        appinst = self.instance()
        if 'length' in self.api.batch:
            return self.api.batch.length(appinst)
        if self.prev_app is not None:
            return self.prev_app.length()
        return 0

    def process(self, index):
        use_cache = self.use_cache()
        appinst = self.instance()
        appinst.set_batch_index(index)

        if use_cache:
            cached_batch = self.cache.get(index)
            if cached_batch is not None:
                return cached_batch

        # process batch
        result = self.api.batch.process(appinst)
        if use_cache:
            self.cache.set(index, result)
        return result

    def view(self, config=dict()):
        config = stdClass(config)
        wf_id = self.__workflowid__
        app_id = self.id()
        html = self.__view__.html
        js = self.__view__.js
        css = self.__view__.css
        try:
            pug = pypugjs.Parser(html)
            pug = pug.parse()
            html = pypugjs.ext.jinja.Compiler(pug).compile()
        except:
            pass
        
        try:
            css = f"#seasondh-{wf_id}-{app_id} " + "{" + css + "}"
            css = lesscpy.compile(StringIO(css), minify=True)
        except:
            css = ""

        baseurl = config.API_URL
        
        ctrlname = f'seasondh-{wf_id}-{app_id}'
        view = f'<div id="seasondh-{wf_id}-{app_id}" ng-controller="seasondh-{wf_id}-{app_id}">{html}</div>'
        view = view + f"<script>{SEASONDH_JS}</script>"
        view = view + f"<script>var seasondh = season_datahub('{baseurl}', '{wf_id}', '{app_id}');</script>"
        view = view + f'<script>{js}</script>'
        view = view + '<script>try { app.controller("' + ctrlname + '", seasondh_controller); } catch(e) { app.controller("' + ctrlname + '", function() {}); }</script>'
        view = view + f'<style>{css}</style>'
        return view

    def view_api(self, name, framework=stdClass()):
        if self.api.view is None:
            return None
        app = self.instance()
        app.use_cache = self.use_cache
        app.length = self.length

        def batch_api(fnname, index):
            appinst = self.instance()
            appinst.set_batch_index(index)
            proc = Spawner(self.api.batch)
            namespace = self.__workflowid__ + "." + self.id()
            result = proc.run(namespace, fnname, appinst)
            if fnname == 'process':
                self.cache.set(index, result)
            return result
        
        app.batch_api = batch_api
        app.batchAPI = batch_api
        
        result = self.api.view[name](app, framework)
        return result

# instance class for api 
class app_instance:
    def __init__(self, app):
        self.__app__ = app
        self.__batch_index__ = None

    def length(self):
        return len(self.__app__)

    def setBatchIndex(self, index):
        self.set_batch_index(index)

    def set_batch_index(self, index):
        self.__batch_index__ = index

    def batch(self, index=0):
        if self.__batch_index__ is not None:
            return batch(self.__app__, self.__batch_index__)
        return batch(self.__app__, index)

    def config(self, namespace="config"):
        return config_storage(os.path.join(self.__app__.config.path, "config"), f"{namespace}.pkl")

    def data(self):
        path = os.path.join(self.__app__.config.path, "data")
        return base_storage(path)
        
class batch:
    def __init__(self, app, index):
        self.__app__ = app
        self.__batch_index__ = index

    def index(self):
        return self.__batch_index__

    def get(self, copy=False):
        index = self.index()
        if self.__app__.prev_app is None: batch = None
        else: batch = self.__app__.prev_app.process(index)
        if copy == True: batch = copy.deepcopy(batch)
        return batch

    def storage(self):
        index = self.index()
        path = os.path.join(self.__app__.config.path, "batch", f"index_{index}")
        return base_storage(path)

class base_storage(Storage):
    def __init__(self, path):
        super().__init__(path)

    def get(self, name, default=None):
        try:
            return self.read_pickle(str(name))
        except:
            pass
        return default

    def set(self, name, value):
        try:
            self.write_pickle(str(name), value)
        except:
            pass

    def clear(self):
        self.remove(".")

class config_storage:
    def __init__(self, path, namespace):
        self.__storage__ = storage = Storage(path)
        self.__namespace__ = namespace
        try:
            self.__config__ = storage.read_pickle(namespace)
        except:
            self.__config__ = stdClass()

    def get(self, name, default=None):
        try:
            return self.__config__[name]
        except:
            pass
        return default

    def set(self, name, value):
        try:
            self.__config__[name] = value
            self.__storage__.write_pickle(self.__namespace__, self.__config__)
        except:
            pass

    def clear(self):
        self.__storage__.write_pickle(self.__namespace__, stdClass())

    def to_dict(self):
        return dict(self.__config__)

class storage_cache:
    def __init__(self, path):
        self.__storage__ = Storage(os.path.join(path, "cache"))

    def get(self, name, default=None):
        try:
            return self.__storage__.read_pickle("batch_" + str(name) + ".pkl")
        except:
            pass
        return default

    def set(self, name, value):
        try:
            self.__storage__.write_pickle("batch_" + str(name) + ".pkl", value)
        except:
            pass

    def clear(self):
        self.__storage__.remove(".")