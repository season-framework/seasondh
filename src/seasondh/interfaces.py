from abc import ABCMeta, abstractmethod
import pickle

class BaseDataLoader(metaclass=ABCMeta):

    def __init__(self, **kwargs):
        self.kwargs = self.options = kwargs
        self.build(**kwargs)

    def __getitem__(self, index):
        if index >= len(self):
            raise IndexError
        return self.get(index, **self.kwargs)
    
    def __len__(self):
        return self.count(**self.kwargs)
    
    @abstractmethod
    def build(self, **kwargs):
        pass

    @abstractmethod
    def get(self, index, **kwargs):
        pass

    @abstractmethod
    def find(self, **args):
        pass
    
    @abstractmethod
    def count(self, **kwargs):
        pass

class BaseProcess(metaclass=ABCMeta):

    def __init__(self, **kwargs):
        self.kwargs = self.options = kwargs

    def __process__(self, batch, **kwargs):
        return self.process(batch, **kwargs)
    
    @abstractmethod
    def process(self, batch, **kwargs):
        pass
