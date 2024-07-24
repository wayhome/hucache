# -*- coding: utf-8 -*-

"""
Provides serialization mechanisms primarily for data exchange.
"""

__all__ = ["Serializer"]

import datetime
import decimal
import json
import logging
from typing import Any, Union

from packaging import version
import sqlalchemy
from sqlalchemy.ext.declarative import DeclarativeMeta
from sqlalchemy.engine import ResultProxy

try:
    import cPickle as pickle
except ImportError:
    import pickle

    logging.warning("Unable to import cPickle, using pickle instead")


class ObjectDict(dict):
    """Makes a dictionary behave like an object."""

    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError:
            raise AttributeError(name)

    def __setattr__(self, name, value):
        self[name] = value


class Serializer:
    """Serialization handler"""

    SUPPORTED_FORMATS = ["JSON", "PICKLE"]

    def __init__(self, format_type: str = "JSON"):
        """
        Create a serialization handler.

        :param format: Specifies the format for this serialization handler (e.g., JSON, PICKLE).
        """
        format_type = format_type.upper()
        if format_type not in self.SUPPORTED_FORMATS:
            raise ValueError("Unsupported serialization format")
        self.format_type = format_type

    def load(self, stream: Union[str, bytes, Any]) -> Any:
        """
        Load data from the given stream.

        :param stream: The source to load data from. Can be a string, bytes, or file-like object.
        :return: Deserialized data.
        """
        func_name = f"_from_{self.format_type.lower()}"
        return globals()[func_name](stream)

    def dump(self, data: Any) -> Union[str, bytes]:
        """
        Convert the specified data to serialized information.

        :param data: The data to serialize. Usually a mapping or sequence type.
        :return: Serialized data as string or bytes.
        """
        func_name = f"_to_{self.format_type.lower()}"
        return globals()[func_name](data)

    serialize = dump
    unserialize = load
    encode = dump
    decode = load


def _from_pickle(stream: Union[str, bytes, Any]) -> Any:
    """Load data from PICKLE file or string"""
    if isinstance(stream, (str, bytes)):
        return pickle.loads(stream)
    return pickle.load(stream)


def _to_pickle(data: Any) -> bytes:
    """Dump data into a PICKLE string."""
    return pickle.dumps(data)


def _from_json(stream: Union[str, bytes, Any]) -> Any:
    """Load data from a JSON file or string."""
    if isinstance(stream, (str, bytes)):
        return json.loads(stream, object_hook=ObjectDict)
    return json.load(stream, object_hook=ObjectDict)


def _to_json(data: Any) -> str:
    """Dump data into a JSON string."""
    return json.dumps(data, cls=AwareJSONEncoder)


class AwareJSONEncoder(json.JSONEncoder):
    """
    JSONEncoder subclass that handles date/time, decimal types,
    and SQLAlchemy's ResultProxy/RowProxy.
    """

    DATE_FORMAT = "%Y-%m-%d"
    TIME_FORMAT = "%H:%M:%S"

    def default(self, o: Any) -> Any:
        sa_version = version.parse(sqlalchemy.__version__)

        if sa_version < version.parse("1.4"):
            from sqlalchemy.engine import RowProxy
            from sqlalchemy.util._collections import AbstractKeyedTuple

            if isinstance(o, RowProxy):
                return dict(o)
            if isinstance(o, AbstractKeyedTuple):
                return o._asdict()
        else:
            from sqlalchemy.engine import Row

            if isinstance(o, Row):
                return dict(o)
            if isinstance(o, tuple) and hasattr(o, "_fields"):
                return o._asdict()

        if isinstance(o, datetime.datetime):
            return o.strftime(f"{self.DATE_FORMAT} {self.TIME_FORMAT}")
        if isinstance(o, datetime.date):
            return o.strftime(self.DATE_FORMAT)
        if isinstance(o, datetime.time):
            return o.strftime(self.TIME_FORMAT)
        if isinstance(o, decimal.Decimal):
            return str(o)
        if isinstance(o, ResultProxy):
            return list(o)
        if isinstance(o.__class__, DeclarativeMeta):
            return {
                field: value
                for field, value in o.__dict__.items()
                if not field.startswith("_")
            }
        return super().default(o)
