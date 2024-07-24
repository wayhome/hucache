#!/usr/bin/env python
# -*- coding: utf-8 -*-
from abc import ABCMeta, abstractmethod
import six

from redis import StrictRedis

from .constants import NOT_FOUND, DEFAULT_TIMEOUT
from .serializer import Serializer


@six.add_metaclass(ABCMeta)
class AbstractStore(object):
    @abstractmethod
    def get(self, key, default=NOT_FOUND):
        pass

    @abstractmethod
    def set(self, key, value, timeout=DEFAULT_TIMEOUT):
        pass

    @abstractmethod
    def delete(self, *keys):
        pass


class RedisStore(AbstractStore):
    def __init__(self, conn, format_type="JSON"):
        self._conn = conn
        self._serializer = Serializer(format_type=format_type)

    @staticmethod
    def from_url(url, format_type="JSON"):
        conn = StrictRedis.from_url(url)
        return RedisStore(conn, format_type)

    def get(self, key, default=NOT_FOUND):
        data = self._conn.get(key)
        if data is None:
            return default
        return self._serializer.decode(data)

    def set(self, key, value, timeout=DEFAULT_TIMEOUT):
        data = self._serializer.encode(value)
        self._conn.setex(key, timeout, data)

    def delete(self, *keys):
        self._conn.delete(*keys)
