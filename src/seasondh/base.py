import string
import random

class stdClass(dict):
    def __init__(self, *args, **kwargs):
        super(stdClass, self).__init__(*args, **kwargs)
        for arg in args:
            if isinstance(arg, dict):
                for k, v in arg.iteritems():
                    self[k] = v

        if kwargs:
            for k, v in kwargs.iteritems():
                self[k] = v

    def __getattr__(self, attr):
        return self.get(attr)

    def __setattr__(self, key, value):
        self.__setitem__(key, value)

    def __setitem__(self, key, value):
        super(stdClass, self).__setitem__(key, value)
        self.__dict__.update({key: value})

    def __delattr__(self, item):
        self.__delitem__(item)

    def __delitem__(self, key):
        super(stdClass, self).__delitem__(key)
        del self.__dict__[key]

    def __getstate__(self): 
        return self

    def __setstate__(self, d): 
        self.__dict__.update(d)

class Configuration(dict):
    def __init__(self, *args, **kwargs):
        super(Configuration, self).__init__(*args, **kwargs)

    def __getattr__(self, attr):
        try:
            return self.get(attr)
        except:
            return None

    def __setattr__(self, key, value):
        self.__setitem__(key, value)

    def __setitem__(self, key, value):
        super(stdClass, self).__setitem__(key, value)
        self.__dict__.update({key: value})

    def __delattr__(self, item):
        self.__delitem__(item)

    def __delitem__(self, key):
        super(stdClass, self).__delitem__(key)
        del self.__dict__[key]

    def __getstate__(self): 
        return self

    def __setstate__(self, d): 
        self.__dict__.update(d)

def randomstring(length=12):
    string_pool = string.ascii_letters + string.digits
    result = ""
    for i in range(length):
        result += random.choice(string_pool)
    return result

import multiprocessing as mp
import time
import traceback
from io import StringIO 
import sys

mp.set_start_method('fork')

processes = {}

class Capturing(list):

    def __enter__(self):
        self._stdout = sys.stdout
        sys.stdout = self._stringio = StringIO()
        return self

    def __exit__(self, *args):
        self.extend(self._stringio.getvalue().splitlines())
        del self._stringio
        sys.stdout = self._stdout

class Spawner:

    def __init__(self, name="default spawner"):
        self.name = name

    def define(self, code):
        self.code = code

    def fnwrap(self, q, fnname, **kwargs):
        result = None
        stderr = ""
        with Capturing() as stdout:
            try:
                code = self.code
                fn = {'__file__': 'seasondh.Spawner', '__name__': 'seasondh.Spawner'}
                exec(compile(code, 'seasondh.Spawner', 'exec'), fn)
                result = fn[fnname](**kwargs)
            except Exception as e:
                stderr = traceback.format_exc()

        stdout = list(stdout)
        stdout = "\n".join(stdout)
        q.put(result)
        q.put(stdout)
        q.put(stderr)

    def kill(self, dataset_id, app_id):
        process_group = f"{dataset_id}:{app_id}"
        if process_group not in processes:
            return 

        for i in range(len(processes[process_group])):
            p = processes[process_group][i]
            try:
                p.kill()
            except:
                pass
            if p.exitcode is not None:
                processes[process_group].remove(p)
                if i > 0: i = i - 1

    def run(self, dataset_id, app_id, fnname, kwargs=dict()):
        process_group = f"{dataset_id}:{app_id}"
        if process_group not in processes:
            processes[process_group] = []
        
        q = mp.Queue()
        p = mp.Process(target=self.fnwrap, args=[q, fnname], kwargs=kwargs)
        p.name = fnname

        processes[process_group].append(p)
        
        p.start()
        result = q.get()
        stdout = q.get()
        stderr = q.get()
        p.join()

        processes[process_group].remove(p)

        return result, stdout, stderr