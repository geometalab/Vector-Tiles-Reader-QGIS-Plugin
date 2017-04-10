from qgis.core import QgsMessageLog
import logging
import sys


def info(msg, *args):
    _log_message(msg, QgsMessageLog.INFO, *args)


def warn(msg, *args):
    _log_message(msg, QgsMessageLog.WARNING, *args)


def critical(msg, *args):
    _log_message(msg, QgsMessageLog.CRITICAL, *args)


def debug(msg, *args):
    _log_message(msg, None, *args)


def _log_message(msg, level, *args):
    try:
        msg = msg.format(*args)

        if level == QgsMessageLog.INFO:
            logging.info(msg)
        elif level == QgsMessageLog.WARNING:
            logging.warning(msg)
        elif level == QgsMessageLog.CRITICAL:
            logging.critical(msg)
        elif not level:
            logging.debug(msg)
            # TODO: disable after debugging
            level = QgsMessageLog.INFO

        print(msg)
        QgsMessageLog.logMessage(msg, 'Vector Tile Reader', level)
    except:
        print("Something went wrong: {}".format(sys.exc_info()))
