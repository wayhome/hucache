#!/usr/bin/env python
# -*- coding: utf-8 -*-
DEFAULT_TIMEOUT = 3600


class NotFound(object):
    """Describe a missing cache value.

    The :attr:`.NO_VALUE` module global
    should be used.
    """

    __slots__ = tuple()

    def __repr__(self):
        return "NotFound"


NOT_FOUND = NotFound()
