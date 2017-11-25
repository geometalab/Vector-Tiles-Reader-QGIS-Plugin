from future import standard_library
standard_library.install_aliases()
from .log_helper import warn, info

from .vtr_2to3 import *


def url_exists(url):
    reply = get_async_reply(url, head_only=True)
    while not reply.isFinished():
        QApplication.processEvents()

    status = reply.attribute(QNetworkRequest.HttpStatusCodeAttribute)
    result = status == 200
    error = None
    if status != 200:
        error = "HTTP HEAD failed: status {}".format(status)

    return result, error


def get_async_reply(url, head_only=False):
    m = QgsNetworkAccessManager.instance()
    req = QNetworkRequest(QUrl(url))
    if head_only:
        reply = m.head(req)
    else:
        reply = m.get(req)
    return reply


def load_tiles_async(urls_with_col_and_row, on_progress_changed=None, cancelling_func=None):
    replies = [(get_async_reply(url), (col, row)) for url, col, row in urls_with_col_and_row]
    total_nr_of_requests = len(replies)
    all_finished = False
    nr_finished_before = 0
    finished_tiles = set()
    nr_finished = 0
    all_results = []
    cancelling = False
    while not all_finished:
        cancelling = cancelling_func and cancelling_func()
        if cancelling:
            break

        results = []
        new_finished = [r for r in replies if r[0].isFinished() and r[1] not in finished_tiles]
        nr_finished += len(new_finished)
        for reply, tile_coord in new_finished:
            error = reply.error()
            if error:
                info("Error during network request: {}", error)
            else:
                content = reply.readAll().data()
                finished_tiles.add(tile_coord)
                results.append((tile_coord, content))
            reply.deleteLater()
        QApplication.processEvents()
        all_results.extend(results)
        all_finished = nr_finished == total_nr_of_requests
        if nr_finished != nr_finished_before:
            nr_finished_before = nr_finished
            if on_progress_changed:
                on_progress_changed(nr_finished)
    if not all_finished and cancelling:
        unfinished_requests = [r for r in replies if not r[0].isFinished]
        for r in unfinished_requests:
            r.abort()
    if cancelling:
        all_results = []
    return all_results


def load_url(url):
    reply = get_async_reply(url)
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
