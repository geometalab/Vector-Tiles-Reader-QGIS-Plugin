FROM qgis/qgis:latest
MAINTAINER Martin Boos

RUN pip3 install coveralls

RUN qgis_setup.sh vector_tiles_reader && \
    rm -f  /root/.local/share/QGIS/QGIS3/profiles/default/python/plugins/vector_tiles_reader && \
    ln -s /tests_directory/ /root/.local/share/QGIS/QGIS3/profiles/default/python/plugins/vector_tiles_reader