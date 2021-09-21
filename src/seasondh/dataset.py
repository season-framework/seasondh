from .util import randomstring, stdClass, Storage
from .workflow import workflow

class dataset:

    def __init__(self, **kwargs):
        self.workflow = workflow(**kwargs)
        
    def __getitem__(self, index):
        return self.workflow[len(self.workflow)-1][index]

    def __len__(self):
        return len(self.workflow[len(self.workflow)-1])