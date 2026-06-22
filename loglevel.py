import logging
from enum import IntEnum


class LogLevel(IntEnum):
    critical = logging.CRITICAL
    fatal = logging.FATAL
    error = logging.ERROR
    warning = logging.WARNING
    info = logging.INFO
    debug = logging.DEBUG
    notset = logging.NOTSET

    def __str__(self):
        return f'{self.__class__.__name__}.{self.name}'

    @classmethod
    def _missing_(cls, value):
        if type(value) is str:
            value = value.lower()
            if value in dir(cls):
                return cls[value]

        raise ValueError("%r is not a valid %s" % (value, cls.__name__))