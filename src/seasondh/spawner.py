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
    def __init__(self, fn):
        self.fn = fn

    def fnwrap(self, q, fnname, obj):
        result = None
        stderr = ""
        # with Capturing():
        try:
            result = self.fn[fnname](obj)
        except Exception as e:
            stderr = traceback.format_exc()

        q.put(result)

    def kill(self, namespace):
        process_group = namespace
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

    def run(self, namespace, fnname, obj):
        process_group = namespace
        if process_group not in processes:
            processes[process_group] = []
        
        q = mp.Queue()
        p = mp.Process(target=self.fnwrap, args=[q, fnname, obj])
        p.name = fnname

        processes[process_group].append(p)
        
        p.start()
        result = q.get()
        p.join()

        processes[process_group].remove(p)
        return result