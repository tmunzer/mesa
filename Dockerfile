FROM python:3

LABEL maintainer="tmunzer@juniper.net"
LABEL one.stag.mesa.version="1.2.0"
LABEL one.stag.mesa.release-date="2020-02-27"

COPY ./src /app/

WORKDIR /app
RUN pip install --upgrade pip
RUN pip install --no-cache-dir flask junos-eznc requests

EXPOSE 51360
CMD ["python","-u","/app/mesa.py"]

