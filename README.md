## hucache
A Declarative Caching Library for Human

## Usage

```
Construct a cache instance
>>> redis_client = fakeredis.FakeStrictRedis()
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

Custom timeout

Default timeout is 1 hour, you can change  default timeout at the factory

>>> cache = CacheFactory.from_store_conn("redis", redis_client, prefix="test:", default_timeout=300)

Or you can  change it per function

>>> @cache("add:{a}:{b}", timeout=60)
... def add(a, b, c=1):
...    return a + b + c


```
