from qgis.core import QgsMessageLog
import logging


def info(msg, *args):
    _log_message(msg, QgsMessageLog.INFO, *args)


def warn(msg, *args):
    _log_message(msg, QgsMessageLog.WARNING, *args)


def critical(msg, *args):
    _log_message(msg, QgsMessageLog.CRITICAL, *args)


def debug(msg, *args):
    _log_message(msg, None, *args)


def _log_message(msg, level, *args):
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
