FROM mnboos/qgis-testing-environment:release-2_18
MAINTAINER Martin Boos

ARG QGIS_PLUGINS_DIR

RUN Xvfb :99 &
RUN DISPLAY=:99
ENV DISPLAY=:99

RUN qgis_setup.sh vector_tiles_reader
RUN rm -rf $QGIS_PLUGINS_DIR/vector_tiles_reader
RUN ln -s /vector-tiles-reader $QGIS_PLUGINS_DIR/vector_tiles_reader
RUN apt-get update && \
    apt-get install python-pip -y && \
    pip install coverage && \
    pip install coveralls && \
    pip install mock