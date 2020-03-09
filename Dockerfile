FROM python:3

LABEL maintainer="tmunzer@juniper.net"
LABEL one.stag.mesa.version="1.2.0"
LABEL one.stag.mesa.release-date="2020-02-27"

WORKDIR /app

ENV FLASK_APP mesa.py
ENV FLASK_RUN_HOST 0.0.0.0
ENV FLASK_RUN_PORT=51360
COPY /src/requirements.txt requirements.txt
RUN pip install -r requirements.txt

COPY ./src/ .

EXPOSE 51360
CMD ["flask", "run"]

