from qgis.core import QgsMessageLog
import logging


def info(msg, *args):
    _log_message(msg, QgsMessageLog.INFO, args)


def warn(msg, *args):
    _log_message(msg, QgsMessageLog.WARNING, args)


def critical(msg, *args):
    _log_message(msg, QgsMessageLog.CRITICAL, args)


def debug(msg, *args):
    _log_message(msg, None, args)


def _log_message(msg, level, *args):
    msg = msg.format(args)

    if level == QgsMessageLog.INFO:
        logging.info(msg)
    if level == QgsMessageLog.WARNING:
        logging.warning(msg)
    if level == QgsMessageLog.CRITICAL:
        logging.critical(msg)
    if not level:
        logging.debug(msg)
        print(msg)
        # TODO: disable after debugging
        level = QgsMessageLog.INFO

    if level:
        QgsMessageLog.logMessage(msg, 'Vector Tile Reader', level)
