FROM mnboos/qgis-testing-environment:release-2_18
MAINTAINER Martin Boos

#ARG QGIS_BRANCH
#ENV LEGACY='true'

#RUN apt-get update && \
#    apt-get install Xvfb -y
RUN Xvfb :99 &
RUN DISPLAY=:99
ENV DISPLAY=:99

RUN qgis_setup.sh vector_tiles_reader
RUN rm -rf /root/.qgis2/python/plugins/vector_tiles_reader
RUN ln -s /vector-tiles-reader /root/.qgis2/python/plugins/vector_tiles_reader
#RUN ln -s /vector-tiles-reader /tests_directory
#RUN qgis_testrunner.sh vector_tiles_reader.tests.test_vtreader
