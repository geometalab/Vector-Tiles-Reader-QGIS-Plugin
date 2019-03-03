import logging
import os
import sys
import pkgutil
import importlib
import tempfile
import re
try:
    from qgis.core import QgsApplication
    _qgis_available = True
except ImportError:
    _qgis_available = False
    # _logger.error("QGIS not found for logging")

_KEY_REGEX = re.compile(r"(\?|&)(api_)?key=[^\s?&]*")

_DEBUG = "debug"
_INFO = "info"
_WARN = "warn"
_CRITICAL = "critical"


def remove_key(text):
    return _KEY_REGEX.sub("", text)


def get_temp_dir(path_extension=None):
    vtr_temp_dir = os.path.join(tempfile.gettempdir(), "vector_tiles_reader")
    if not os.path.isdir(vtr_temp_dir):
        os.makedirs(vtr_temp_dir)
    if path_extension:
        vtr_temp_dir = os.path.join(vtr_temp_dir, path_extension)
    return vtr_temp_dir


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
        msg = remove_key(msg.format(*args))

        if level == _INFO:
            _logger.info(msg)
        elif level == _WARN:
            _logger.warning(msg, *args)
        elif level == _CRITICAL:
            _logger.exception(msg)
        elif level == _DEBUG:
            _logger.debug(msg)

        _log_to_qgis(msg, level)
    except:
        _logger.error("Unexpected error during logging: {}", sys.exc_info()[1])
        _logger.error("Original message: '{}', params: '{}'", args)


def _import_qgis():
    if pkgutil.find_loader("qgis.core") is not None:
        return importlib.import_module("qgis.core")
    return None


def _log_to_qgis(msg, level):
    if _qgis_available:
        if level != _DEBUG:
            QgsApplication.messageLog().logMessage(msg, 'Vector Tiles Reader'.format(level))

        # if level == _INFO:
        #     Qgis.Info = qgis.QgsMessageLog.INFO
        # elif level == _WARN:
        #     qgis_level = qgis.QgsMessageLog.WARNING
        # elif level == _CRITICAL:
        #     qgis_level = qgis.QgsMessageLog.CRITICAL


try:
    log_path = get_temp_dir("log.txt")
    temp_dir = os.path.dirname(log_path)

    max_logsize_mb = 4
    if os.path.isfile(log_path) and os.stat(log_path).st_size >= max_logsize_mb*1024*1024:
        os.remove(log_path)

    if not os.path.isfile(log_path):
        open(log_path, 'a').close()

    from imp import reload
    reload(logging)

    logging.basicConfig(
        filename=log_path,
        filemode='a',
        level=logging.INFO,
        format="[%(asctime)s] [%(threadName)-12s] [%(levelname)-8s]  %(message)s")

    # fh = logging.FileHandler(os.path.join(temp_dir, "bla.log"))
    _logger = logging.getLogger()
    # _logger.setLevel(logging.INFO)
    # _logger.addHandler(fh)
except IOError:
    _log_to_qgis("Creating logging config failed: {}".format(sys.exc_info()), _WARN)
