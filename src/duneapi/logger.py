"""
Basic universal log configuration for project

in each file you want to log,
import set_log and configure with
`log = set_log(__name__)`
"""
import logging.config
from logging import Logger


def set_log(name: str) -> Logger:
    """
    :param name: usually the module path __name__
    :return: Configured Logger
    """
    log = logging.getLogger(name)
    try:
        logging.config.fileConfig(fname="logging.conf", disable_existing_loggers=True)
    except KeyError:
        pass
    return log
