FROM python:2.7

RUN apt-get update
RUN apt-get -y upgrade

RUN pip install mechanize
RUN pip install --upgrade google-api-python-client


WORKDIR /opt/googlefit-to-kenpos
