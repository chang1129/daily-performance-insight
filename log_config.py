# -*- coding: utf-8 -*-
"""
Created on Wed Aug 30 14:18:38 2023

@author: cchang
"""

LOGGING_CONFIG = {
    "version": 1,
    "loggers": {
        "": {  # root logger
            "level": "INFO",
            "propagate": False,
            "handlers": ["stream_handler"],
        },
        "custom_logger": {
            "level": "INFO",
            "propagate": False,
            "handlers": ["stream_handler"],
        },
    },
    "handlers": {
        "stream_handler": {
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stdout",
            "level": "DEBUG",
            "formatter": "default_formatter",
        },
        # "file_handler": {
        #     "class": "logging.FileHandler",
        #     "filename": "output.log",
        #     "mode": "a",
        #     "level": "DEBUG",
        #     "formatter": "default_formatter",
        # },
    },
    "formatters": {
        "default_formatter": {
            "format": "%(asctime)s-%(levelname)s-%(name)s::%(module)s::%(funcName)s|%(lineno)s:: %(message)s",
        },
    },
}
