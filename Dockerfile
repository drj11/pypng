FROM ubuntu
RUN apt-get install -y python
ADD code /png/code
WORKDIR /png/code
ENTRYPOINT python -c 'import test_png; test_png.runTest()'
