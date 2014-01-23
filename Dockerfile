FROM ubuntu
RUN apt-get install -y python
ADD code /png/code
ENTRYPOINT cd /png/code; python -c 'import test_png; test_png.runTest()'
