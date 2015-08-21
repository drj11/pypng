FROM ubuntu
RUN apt-get update && apt-get install -y python python3.4
ADD . /png
WORKDIR /png
RUN python setup.py install
RUN python3 setup.py install
# ENTRYPOINT python -c 'import test_png; test_png.runTest()'
