from future import standard_library
standard_library.install_aliases()
from log_helper import warn
from qgis.core import QgsNetworkAccessManager

from PyQt4.QtGui import QApplication
from PyQt4.QtCore import QUrl
from PyQt4.QtNetwork import QNetworkRequest


def url_exists(url):
    reply = load_url_async(url, head_only=True)
    while not reply.isFinished():
        QApplication.processEvents()

    status = reply.attribute(QNetworkRequest.HttpStatusCodeAttribute)
    result = status == 200
    error = None
    if status != 200:
        error = "HTTP HEAD failed: status {}".format(status)

    return result, error


def load_url_async(url, head_only=False):
    m = QgsNetworkAccessManager.instance()
    req = QNetworkRequest(QUrl(url))
    req.setRawHeader('User-Agent', 'Magic Browser')
    if head_only:
        reply = m.head(req)
    else:
        reply = m.get(req)
    return reply


def load_url(url):
    reply = load_url_async(url)
    while not reply.isFinished():
        QApplication.processEvents()

    http_status_code = reply.attribute(QNetworkRequest.HttpStatusCodeAttribute)
    if http_status_code == 200:
        content = reply.readAll().data()
    else:
        if http_status_code is None:
            content = "Request failed: {}".format(reply.errorString())
        else:
            content = "Request failed: HTTP status {}".format(http_status_code)
        warn(content)
    return http_status_code, content
