FROM ubuntu:20.04 as downloader
ARG SPEEDTEST_VERSION
WORKDIR /opt/speedtest
RUN apt update && apt install -y curl && curl https://raw.githubusercontent.com/sivel/speedtest-cli/$SPEEDTEST_VERSION/speedtest.py -L -o speedtest
RUN chmod +x speedtest

FROM python:3.7.10-slim-buster
WORKDIR /opt/speedtest/
COPY ./entrypoint.sh entrypoint.sh
COPY --from=downloader /opt/speedtest/speedtest /opt/speedtest/
ENTRYPOINT [ "./entrypoint.sh" ]
