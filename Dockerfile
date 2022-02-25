FROM locustio/locust:latest

COPY requirements.txt ./requirements.txt

USER root
RUN apt update && apt install -y git gcc

RUN python -m pip install --upgrade pip
RUN python -m pip install -r requirements.txt

USER locust