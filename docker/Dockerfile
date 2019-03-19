ARG QGIS_TAG
FROM qgis/qgis:${QGIS_TAG}
MAINTAINER Martin Boos

RUN qgis_setup.sh vector_tiles_reader && \
    rm -f  /root/.local/share/QGIS/QGIS3/profiles/default/python/plugins/vector_tiles_reader && \
    ln -s /tests_directory/ /root/.local/share/QGIS/QGIS3/profiles/default/python/plugins/vector_tiles_reader