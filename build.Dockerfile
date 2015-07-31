FROM ubuntu
RUN apt-get update && apt-get install -y python python-pip zip
RUN pip install sphinx
ADD . /pypng
WORKDIR /pypng
RUN sphinx-build -N -d sphinx-crud -a man html
RUN python setup.py sdist
WORKDIR html
# ENTRYPOINT tar cf - build
