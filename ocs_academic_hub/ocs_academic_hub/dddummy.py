#
import sys
from unittest.mock import Mock, MagicMock
from functools import wraps
sys.modules['ddtrace'] = MagicMock()
from ddtrace import tracer

def wrap(a, b):
    def decorator(func):
        @wraps(func)
        def func_wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        return func_wrapper
    return decorator
    
tracer.wrap = wrap
tracer.current_span = lambda: None
    
class C(object):
    def __init__(self, s):
        self._service = s

    @property
    def service(self):
        return self._service

    @service.setter
    def service(self, value):
        self._service = value

    @service.deleter
    def service(self):
        del self._service
                
                
class ContextManager(): 
    def __init__(self, a): 
        # print(f'init method called {a}')
        self._o = C(a)
          
    def __enter__(self): 
        # print('enter method called {}') 
        return self._o
      
    def __exit__(self, exc_type, exc_value, exc_traceback): 
        # print('exit method called') 
        pass
                
tracer.trace = ContextManager
    