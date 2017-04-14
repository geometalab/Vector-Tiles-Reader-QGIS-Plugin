import logging
import sys
import pkgutil
import importlib

_DEBUG = "debug"
_INFO = "info"
_WARN = "warn"
_CRITICAL = "critical"
_qgis_available = None


def info(msg, *args):
    _log_message(msg, _INFO, *args)


def warn(msg, *args):
    _log_message(msg, _WARN, *args)


def critical(msg, *args):
    _log_message(msg, _CRITICAL, *args)


def debug(msg, *args):
    _log_message(msg, _DEBUG, *args)


def _log_message(msg, level, *args):
    try:
        msg = msg.format(*args)

        if level == _INFO:
            logging.info(msg)
        elif level == _WARN:
            logging.warning(msg)
        elif level == _CRITICAL:
            logging.critical(msg)
        elif level == _DEBUG:
            logging.debug(msg)
            print(msg)

        _log_to_qgis(msg, level)
    except:
        print("Something went wrong: {}".format(sys.exc_info()))


def _import_qgis():
    if pkgutil.find_loader("qgis.core") is not None:
        return importlib.import_module("qgis.core")
    return None


def _log_to_qgis(msg, level):
    qgis = _import_qgis()
    if not qgis:
        return

    qgis_level = None
    if level == _DEBUG:
        pass
    elif level == _INFO:
        qgis_level = qgis.QgsMessageLog.INFO
    elif level == _WARN:
        qgis_level = qgis.QgsMessageLog.WARN
    elif level == _CRITICAL:
        qgis_level = qgis.QgsMessageLog.CRITICAL

    if qgis_level is not None:
        qgis.QgsMessageLog.logMessage(msg, 'Vector Tile Reader', qgis_level)
