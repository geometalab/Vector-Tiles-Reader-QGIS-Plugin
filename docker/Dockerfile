FROM mnboos/qgis-testing-environment:qgis3
MAINTAINER Martin Boos

RUN Xvfb :99 &
RUN DISPLAY=:99
ENV DISPLAY=:99

RUN qgis_setup.sh vector_tiles_reader
RUN rm -rf /root/.qgis2/python/plugins/vector_tiles_reader
RUN ln -s /vector-tiles-reader /root/.qgis2/python/plugins/vector_tiles_reader
RUN apt-get update && \
    apt-get install python3-pip -y && \
    pip3 install coverage && \
    pip3 install coveralls && \
    pip3 install mock