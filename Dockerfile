FROM python:3

COPY ./src /app/

WORKDIR /app
RUN pip install --upgrade pip
RUN pip install --no-cache-dir flask junos-eznc requests

EXPOSE 51360
ENTRYPOINT python -u /app/mesa.py 51360

