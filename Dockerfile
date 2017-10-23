FROM elpaso/qgis-testing-environment
MAINTAINER Martin Boos

ENV LEGACY='true'

RUN apt-get install Xvfb
RUN Xvfb :99 &
RUN DISPLAY=:99
ENV DISPLAY=:99

RUN mkdir vector-tiles-reader
RUN ln -s /vector-tiles-reader /tests_directory

RUN qgis_setup.sh vector_tiles_reader
RUN ln -s /vector-tiles-reader /root/.qgis2/python/plugins/vector_tiles_reader
#RUN qgis_testrunner.sh vector_tiles_reader.test_vtreader
