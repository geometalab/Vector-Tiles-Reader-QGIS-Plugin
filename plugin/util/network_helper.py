from time import sleep
from typing import Callable, List, Optional, Tuple

from PyQt5.QtCore import QUrl
from PyQt5.QtNetwork import QNetworkReply, QNetworkRequest
from PyQt5.QtWidgets import QApplication
from qgis.core import QgsNetworkAccessManager

from .log_helper import info, remove_key, warn


def url_exists(url: str) -> Tuple[bool, Optional[str], str]:
    reply = http_get_async(url, head_only=True)
    while not reply.isFinished():
        QApplication.processEvents()

    status = reply.attribute(QNetworkRequest.HttpStatusCodeAttribute)
    if status == 301:
        location = reply.header(QNetworkRequest.LocationHeader).toString()
        if location != url:
            info("Moved permanently, new location is: {}", location)
            return url_exists(location)

    success: bool = status == 200
    error: Optional[str] = None
    info("URL check for '{}': status '{}'", url, status)
    if not success:
        if not status:
            error = reply.errorString()
        if status == 302:
            error = "Loading error: Moved Temporarily.\n\nURL incorrect? Missing or incorrect API key?"
        elif status == 404:
            error = "Loading error: Resource not found.\n\nURL incorrect?"
        elif error:
            error = "Loading error: {}\n\nURL incorrect? (HTTP Status {})".format(error, status)
        else:
            error = "Something went wrong with '{}'. HTTP Status is {}".format(remove_key(url), status)

    return success, error, url


def http_get_async(url: str, head_only: bool = False) -> QNetworkReply:
    m = QgsNetworkAccessManager.instance()
    req = QNetworkRequest(QUrl(url))
    if head_only:
        reply = m.head(req)
    else:
        reply = m.get(req)
    return reply


def load_tiles_async(
    urls_with_col_and_row, on_progress_changed: Callable = None, cancelling_func: Callable[[], bool] = None
) -> List:
    replies: List[Tuple[QNetworkReply, Tuple[int, int]]] = [
        (http_get_async(url), (col, row)) for url, col, row in urls_with_col_and_row
    ]
    total_nr_of_requests = len(replies)
    all_finished = False
    nr_finished_before = 0
    finished_tiles = set()
    nr_finished = 0
    all_results = []
    cancelling = False
    while not all_finished:
        sleep(0.075)
        cancelling: bool = cancelling_func and cancelling_func()
        if cancelling:
            break

        results = []
        new_finished = list(filter(lambda r: r[0].isFinished() and r[1] not in finished_tiles, replies))
        nr_finished += len(new_finished)
        for reply, tile_coord in new_finished:
            finished_tiles.add(tile_coord)
            if reply.error():
                warn(
                    "Error during network request: {}, {}",
                    remove_key(reply.errorString()),
                    remove_key(reply.url().toDisplayString()),
                )
            else:
                content = reply.readAll().data()
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
        unfinished_requests = [reply for reply, tile_coord in replies if not reply.isFinished]
        for r in unfinished_requests:
            r.abort()
    if cancelling:
        all_results = []
    return all_results


def http_get(url: str) -> Tuple[int, str]:
    reply = http_get_async(url)
    while not reply.isFinished():
        QApplication.processEvents()

    http_status_code = reply.attribute(QNetworkRequest.HttpStatusCodeAttribute)
    if http_status_code == 200:
        content = reply.readAll().data()
        # todo: rather get content type from response than from file extension
        if url.endswith(".json") and isinstance(content, bytes):
            content = content.decode("utf-8")
    else:
        if http_status_code is None:
            content = "Request failed: {}".format(reply.errorString())
        else:
            content = "Request failed: HTTP status {}".format(http_status_code)
        warn(content)
    return http_status_code, content
