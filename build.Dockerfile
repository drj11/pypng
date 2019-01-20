FROM ubuntu
RUN apt-get update && apt-get install -y python python-pip zip
ENV PYTHONDONTWRITEBYTECODE=x
RUN pip install sphinx
WORKDIR /pypng
