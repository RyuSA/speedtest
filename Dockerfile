FROM busybox:stable as downloader
ARG SPEEDTEST_VERSION
WORKDIR /opt/speedtest
RUN wget https://raw.githubusercontent.com/sivel/speedtest-cli/${SPEEDTEST_VERSION}/speedtest.py -O speedtest
RUN chmod +x speedtest

FROM python:3.7.10-slim-buster
WORKDIR /opt/speedtest/
COPY ./entrypoint.sh entrypoint.sh
COPY --from=downloader /opt/speedtest/speedtest /opt/speedtest/
ENTRYPOINT [ "./entrypoint.sh" ]
