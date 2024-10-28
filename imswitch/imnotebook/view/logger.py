
import logging

_logger = None


def log(message):
    if _logger is not None:
        try:
            _logger(str(message).strip())
        except Exception as e:
            logging.debug(e)


def set_logger(logger):
    global _logger
    _logger = logger


def setup_logging(logfile=None, logfileformat = '[%(levelname)s] (%(threadName)-10s) %(message)s'):
    # try to open a file in the current directory
    if logfile is None:
        logging.basicConfig(level=logging.DEBUG, filename=logfile, format=logfileformat)
    else:
        logging.basicConfig(level=logging.DEBUG, format=logfileformat)
    global _logger
    _logger = lambda message: logging.debug(message)
