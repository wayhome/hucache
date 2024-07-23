# -*- coding: utf-8 -*-

"""
提供主要用于数据交换的序列化处理机制。
"""

__all__ = ["Serializer"]

import datetime
import decimal
import json
import logging
import six
from packaging import version

try:
    import cPickle as pickle
except ImportError:
    import pickle

    logging.warning("can't import cpickle, use pickle instead")


class ObjectDict(dict):
    """Makes a dictionary behave like an object."""

    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError:
            raise AttributeError(name)

    def __setattr__(self, name, value):
        self[name] = value

    def __delattr__(self, name):
        del self[name]


class Serializer(object):
    """序列化处理器"""

    #: 支持的序列化格式。
    SUPPORTED_FORMATS = ["JSON", "PICKLE"]

    def __init__(self, format="JSON"):
        """创建一个序列化处理器。

        :param str format: 指定该序列化处理器采用的格式，如 YAML、JSON 等。
        """
        format = format.upper()
        if format in self.SUPPORTED_FORMATS:
            self.format = format
        else:
            raise ValueError("unsupported serializaion format")

    def load(self, stream):
        """从参数 ``stream`` 中获取数据。

        :param stream: 要载入数据的来源。可以是字符串或文件等类型。
        :type stream: mixed
        :rtype: str|unicode|file
        """
        func_name = "".join(["_from_", self.format.lower()])
        func = globals()[func_name]
        return func(stream)

    def dump(self, data):
        """将指定数据 ``data`` 转换为序列化后的信息。

        :param data: 要序列化的数据。通常是某种映射或序列类型。
        :type data: mixed
        :rtype: str|unicode
        """
        func_name = "".join(["_to_", self.format.lower()])
        func = globals()[func_name]
        return func(data)

    def serialize(self, data):
        """:meth:`dump` 方法的别名。"""
        return self.dump(data)

    def unserialize(self, stream):
        """:meth:`load` 方法的别名。"""
        return self.load(stream)

    def encode(self, data):
        """:meth:`dump` 方法的别名。"""
        return self.dump(data)

    def decode(self, stream):
        """:meth:`load` 方法的别名。"""
        return self.load(stream)


def _from_pickle(stream):
    """Load data from PICKLE file or string"""
    if isinstance(stream, six.string_types):
        data = pickle.loads(stream)
    else:
        data = pickle.load(stream)
    return data


def _to_pickle(data):
    """Dump data into a PICKLE string."""
    return pickle.dumps(data)


def _from_json(stream):
    """Load data form a JSON file or string."""
    if isinstance(stream, six.string_types) or isinstance(stream, six.binary_type):
        data = json.loads(stream, object_hook=lambda d: ObjectDict(d))
    else:
        data = json.load(stream, object_hook=lambda d: ObjectDict(d))
    return data


def _to_json(data):
    """Dump data into a JSON string."""
    return json.dumps(data, cls=AwareJSONEncoder)


class AwareJSONEncoder(json.JSONEncoder):
    """JSONEncoder subclass that knows how to encode date/time and
    decimal types, and also ResultProxy/RowProxy of SQLAlchemy.
    """

    DATE_FORMAT = "%Y-%m-%d"
    TIME_FORMAT = "%H:%M:%S"

    def default(self, o):
        import sqlalchemy
        from sqlalchemy.ext.declarative import DeclarativeMeta
        from sqlalchemy.engine import ResultProxy
        sa_version = version.parse(sqlalchemy.__version__)

        # Handling for SQLAlchemy versions before 1.4
        if sa_version < version.parse("1.4"):
            from sqlalchemy.engine import ResultProxy, RowProxy
            from sqlalchemy.util._collections import AbstractKeyedTuple

            if isinstance(o, RowProxy):
                return dict(o)
            elif isinstance(o, AbstractKeyedTuple):
                return o._asdict()

        # Handling for SQLAlchemy 1.4 and above
        if sa_version >= version.parse("1.4"):
            from sqlalchemy.engine import Row

            if isinstance(o, Row):
                return dict(o)
            elif isinstance(o, tuple) and hasattr(o, '_fields'):  # namedtuple
                return o._asdict()

        if isinstance(o, datetime.datetime):
            # d = datetime_safe.new_datetime(o)
            # return d.strftime("%s %s" % (self.DATE_FORMAT, self.TIME_FORMAT))
            return o.strftime("%s %s" % (self.DATE_FORMAT, self.TIME_FORMAT))
        elif isinstance(o, datetime.date):
            # d = datetime_safe.new_date(o)
            return o.strftime(self.DATE_FORMAT)
        elif isinstance(o, datetime.time):
            return o.strftime(self.TIME_FORMAT)
        elif isinstance(o, decimal.Decimal):
            return str(o)
        elif isinstance(o, ResultProxy):
            return list(o)
        elif isinstance(o.__class__, DeclarativeMeta):
            fields = {}
            instance_dict = o.__dict__
            for field in instance_dict:
                if not field.startswith("_"):
                    fields[field] = instance_dict[field]
            return fields
        else:
            return super(AwareJSONEncoder, self).default(o)
