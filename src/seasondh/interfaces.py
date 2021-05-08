from abc import ABCMeta, abstractmethod
import pickle

class BaseDataLoader(metaclass=ABCMeta):

    def __init__(self, **kwargs):
        self.options = kwargs
        self.build(**kwargs)

    def __getitem__(self, index):
        if index >= len(self):
            raise IndexError
        return self.get(index)
    
    def __len__(self):
        return self.count()
    
    @abstractmethod
    def build(self, **kwargs):
        pass

    @abstractmethod
    def get(self, index):
        pass

    @abstractmethod
    def find(self, **args):
        pass
    
    @abstractmethod
    def count(self):
        pass

class BaseProcess(metaclass=ABCMeta):

    def __init__(self, **kwargs):
        self.options = kwargs
    
    @abstractmethod
    def process(self, batch):
        pass
