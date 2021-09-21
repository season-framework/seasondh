import os
from .util import stdClass
from .version import VERSION_STRING
from .workflow import workflow
from .dataset import dataset

VERSION = __version__ = version = VERSION_STRING

def load(basepath):
    seasondh = stdClass()
    def _workflow(**kwargs):
        kwargs = stdClass(kwargs)
        if kwargs.id is None: raise("`id` not defined")
        kwargs.basepath = os.path.join(basepath, kwargs.id)
        return workflow(**kwargs)

    def _dataset(**kwargs):
        kwargs = stdClass(kwargs)
        if kwargs.id is None: raise("`id` not defined")
        kwargs.basepath = os.path.join(basepath, kwargs.id)
        return dataset(**kwargs)

    seasondh.workflow = _workflow
    seasondh.dataset = _dataset
    return seasondh