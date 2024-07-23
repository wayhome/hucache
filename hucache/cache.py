#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Define a store class, which  contains the `get` and `set` method
>>> from .store import RedisStore
>>> import fakeredis
>>> redis_client = fakeredis.FakeStrictRedis()

Construct a cache instance
>>> cache = CacheFactory.from_store_conn("redis", redis_client)

Use the cache on function

>>> @cache("add:{a}:{b}")
... def add(a, b, c=1):
...    return a + b + c
>>> add(3, 2)
6

The third argument c is not used in the cache key "add:{a}:{b}",
so the result will not change.
>>> add(3, b=3)
7
>>> add(3, b=3, c=2)
7
>>> add.invalidate(3, 3)
>>> add(3, b=3, c=2)
8

You can use positional argument or keywords argument as you wish.
>>> @cache("mul:{a}:{b}:{c}")
... def mul(a, b, c=2):
...   return a * b * c
>>> mul(3, 4)
24
>>> mul(3, 4) == mul(3, c=2, b=4) == mul(c=2, a=3, b=4) == mul(3, 4, 2)
True

Use the cache on class

>>> class Example(object):
...   def __init__(self, incr):
...       self.incr = incr
...   @cache("example.add:{a}:{b}:{c}")
...   def add(self, a, b, c=1):
...       return a + b + c + self.incr
...   @cache("example.mul:{a}:{b}:{c}")
...   @classmethod
...   def mul(cls, a, b, c=2):
...       return a * b * c

>>> Example(1).add(2, 3)
7
>>> Example(2).add(a=2, b=3) == Example(3).add(b=3, c=1, a=2)
True
>>> Example.mul(3,4)
24
>>> Example.mul(3,4) == Example.mul(3, b=4, c=2) == Example.mul(b=4,c=2,a=3)
True

>>> @cache("add_ref:{a.id}:{b.id}")
... def add_ref(a, b, c=1):
...    return a.id + b.id + c
>>> from collections import namedtuple
>>> Point = namedtuple('Point', 'id')
>>> add_ref(Point(3), Point(4))
8
"""
import sys
import types

if sys.version_info >= (3, 11):
    from inspect import getfullargspec as getargspec
else:
    from inspect import getargspec

from .store import RedisStore
from .constants import NOT_FOUND, DEFAULT_TIMEOUT


class Cache(object):
    def __init__(self, store, prefix, func, ruler, timeout):
        self._store = store
        self._prefix = prefix
        self._func = func
        self._ruler = ruler
        self._timeout = timeout

    def __get__(self, instance, owner):
        wrapped_self = object.__new__(self.__class__)
        wrapped_self.__dict__ = self.__dict__.copy()
        if instance is None:
            if not hasattr(self._func, "__call__"):
                wrapped_self._func = self._func.__get__(None, owner)
            return wrapped_self
        if not isinstance(self._func, types.MethodType):
            wrapped_self._func = self._func.__get__(instance, owner)
        return wrapped_self

    def __call__(self, *args, **kwargs):
        kwargs = self.__prune_arguments(*args, **kwargs)
        cache_key = self._ruler.format(**kwargs)
        if self._prefix:
            cache_key = self._prefix + cache_key
        result = self._store.get(cache_key)
        if result is NOT_FOUND:
            result = self._func(**kwargs)
            self._store.set(cache_key, result, self._timeout)
        return result

    def __prune_arguments(self, *args, **kwargs):
        arg_spec = getargspec(self._func)
        arg_names = arg_spec.args
        defaults = arg_spec.defaults
        if args:
            if isinstance(self._func, types.MethodType):
                kwargs.update(dict(zip(arg_names[1:], args)))
            else:
                kwargs.update(dict(zip(arg_names, args)))
        if defaults:
            for pos, value in enumerate(defaults):
                argname = arg_names[-len(defaults) + pos]
                if argname not in kwargs:
                    kwargs[argname] = value
        return kwargs

    def invalidate(self, *args, **kwargs):
        kwargs = self.__prune_arguments(*args, **kwargs)
        cache_key = self._ruler.format(**kwargs)
        if self._prefix:
            cache_key = self._prefix + cache_key
        self._store.delete(cache_key)


class CacheFactory(object):
    def __init__(self, store, prefix=None, default_timeout=DEFAULT_TIMEOUT):
        self._store = store
        self._prefix = prefix
        self._default_timeout = default_timeout

    @staticmethod
    def from_store_url(
        store_type, store_url, prefix=None, default_timeout=DEFAULT_TIMEOUT
    ):
        if store_type == "redis":
            store = RedisStore.from_url(store_url)
            return CacheFactory(store, prefix, default_timeout).cache
        else:
            raise NotImplementedError

    @staticmethod
    def from_store_conn(store_type, conn, prefix=None, default_timeout=DEFAULT_TIMEOUT):
        if store_type == "redis":
            store = RedisStore(conn)
            return CacheFactory(store, prefix, default_timeout).cache
        else:
            raise NotImplementedError

    def cache(self, ruler, timeout=None):
        def wrapper(func):
            return Cache(
                self._store, self._prefix, func, ruler, timeout or self._default_timeout
            )

        return wrapper


if __name__ == "__main__":
    import doctest

    doctest.testmod()
