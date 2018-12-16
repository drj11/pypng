FROM ubuntu
RUN apt-get install -y python
ADD code /png/code
WORKDIR /png/code
ENTRYPOINT python -m test_png
