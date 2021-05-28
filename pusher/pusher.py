"""Pusher

Pusher is a tool that formats the test results from Speedtest and sends the metrics to the Prometheus Pushgateway.

"""
from typing import Dict
from watchdog.events import FileModifiedEvent, FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer

from prometheus_client import CollectorRegistry, Gauge, push_to_gateway
from prometheus_client.exposition import generate_latest

import json
from logging import StreamHandler, getLogger
from logging import INFO as DEFAULT_LOGGING_LEVEL

logger = getLogger(__name__)
handler = StreamHandler()
handler.setLevel(DEFAULT_LOGGING_LEVEL)
logger.setLevel(DEFAULT_LOGGING_LEVEL)
logger.addHandler(handler)

class SpeedtestResult:
    """Type for Speedtest's result
    SpeedtestResult represents the json schema for `speedtest --json`.

    Attributes:
        snip
    """

    testid: str
    ip: str
    sponsor: str
    country: str
    download: float
    upload: float
    ping: float


class PusherOpitons:
    """options
    Pusher's options. 
    """

    # the file path which Pusher watches.
    # you can set this value to set environment value `TARGET_FILE_PATH`
    target_file_path: str

    # Pusher doesn't watch the file more than this value.
    # you can set this value to set environment value `MAX_TIMEOUT`
    # default: 60
    timeout: int

    # Prometheus Pushgateway's job_name
    # Pusher will push metrics to Pushgateway with this job_name
    # you can set this value to set environment value `JOB_NAME`
    job_name: str

    # Prometheus Pushgateway's host
    # Pusher will push metrics there
    # you can set this value to set environment value `PUSHGATEWAY_HOST`
    pushgateway_host: str

    def __init__(self) -> None:
        import os
        self.target_file_path = os.getenv("TARGET_FILE_PATH")
        if self.target_file_path is None:
            raise ValueError("you must set TARGET_FILE_PATH, but None")
        logger.info("TARGET_FILE_PATH: %s", self.target_file_path)

        timeout = os.getenv("MAX_TIMEOUT", "60")
        if timeout is None or not timeout.isdecimal():
            raise ValueError("you must set integer MAX_TIMEOUT, but not")
        self.timeout = int(timeout)
        logger.info("MAX_TIMEOUT: %s", self.timeout)

        self.job_name = os.getenv("JOB_NAME", "speedtest")
        logger.info("JOB_NAME: %s", self.job_name)

        self.pushgateway_host = os.getenv("PUSHGATEWAY_HOST")
        if self.pushgateway_host is None:
            raise ValueError("you must set PUSHGATEWAY_HOST, but None")
        logger.info("PUSHGATEWAY_HOST: %s", self.pushgateway_host)


class Parser:
    """Parser
    """

    @staticmethod
    def parse(jsondata: any) -> SpeedtestResult:
        """make raw result into `SpeedtestResult`

        Args:
            jsondata (any): raw json data.

        """
        result = SpeedtestResult()
        result.testid = jsondata["server"]["id"]
        result.ip = jsondata["client"]["ip"]
        result.country = jsondata["client"]["country"]
        result.download = float(jsondata["download"])
        result.upload = float(jsondata["upload"])
        result.ping = float(jsondata["ping"])
        result.sponsor = jsondata["server"]["sponsor"]
        return result


class Metrics:
    """Prometheus format metrics
    Metrics can import metrics from SpeedtestResult and register it to CollectorRegistry
    """

    # metrics datastore
    # expected: {"speedtest_download_bytes_per_sec": <a gouge>, ...}
    __metrics: Dict[str, Gauge]
    DOWNLOAD = "speedtest_download_bytes_per_sec"
    UPLOAD = "speedtest_upload_bytes_per_sec"
    PING = "speedtest_ping_msec"

    def __init__(self, registry: CollectorRegistry) -> None:
        """constructor

        Args:
            registry(CollectorRegistry): some metrics will be added to this registry.

        """

        default_labels = ["id", "ip", "country", "sponsor"]
        self.__metrics = {}
        self.__register_metrics(
            self.DOWNLOAD, "download", default_labels, registry)
        self.__register_metrics(
            self.UPLOAD, "upload", default_labels, registry)
        self.__register_metrics(
            self.PING, "ping", default_labels, registry)

    def __register_metrics(self, name: str, description: str, labels: list, registry: CollectorRegistry) -> Gauge:
        g = Gauge(name, description, labels, registry=registry)
        self.__metrics[name] = g

    def setResult(self, result: SpeedtestResult) -> None:
        """import speedtest result and set to metrics.

        Args:
            result(SpeedtestResult): the speedtest result.

        """
        label_values = [result.testid, result.ip,
                        result.country, result.sponsor]
        self.__metrics[self.DOWNLOAD].labels(
            *label_values).set(result.download)
        self.__metrics[self.UPLOAD].labels(*label_values).set(result.upload)
        self.__metrics[self.PING].labels(*label_values).set(result.ping)


class Executer:
    """Executer pushes metrics to Prometheus Pushgateway.

    Attributes:
        __pushgateway_host(str) : the hostname of Pushgateway
        __job_name              : the job name of Pushgateway

    """
    __pushgateway_host: str
    __job_name: str

    def __init__(self, options: PusherOpitons) -> None:
        """constructor

        Args:
            options(PusherOptions): options

        """
        self.__pushgateway_host = options.pushgateway_host
        self.__job_name = options.job_name

    def run(self, registry: CollectorRegistry) -> None:
        """push metrics to Pushgateway

        Args:
            registry(CollectorRegistry): Executer pushes metrics using this `registry` 

        Todo:
            logging

        """
        logger.debug(generate_latest(registry=registry).decode("utf-8"))
        push_to_gateway(self.__pushgateway_host,
                        job=self.__job_name, registry=registry)


class Pusher(FileSystemEventHandler):
    """Pusher
    """
    __target: str
    __executer: Executer
    __registry: CollectorRegistry
    __metrics: Metrics
    __observer: Observer

    def __init__(self, options: PusherOpitons, executer: Executer, observer: Observer) -> None:
        """constructor

        Args:
            options(PusherOpitons)  : options
            executer(Executer)      : Pusher executes this executer when the target file updated.
            observer(Observer)      : Pusher call `observer.stop()` after executer run.

        """
        super().__init__()
        self.__target = options.target_file_path
        self.__executer = executer
        self.__observer = observer
        self.__registry = CollectorRegistry()
        self.__metrics = Metrics(self.__registry)

    def on_modified(self, event: FileSystemEvent) -> None:
        """will be called when the target file changes
        Pusher gain the speedtest result and push it to Pushgateway as a metrics

        Args:
            event(FileSystemEvent): FileSystemEvent, this argument will be injected by the parent's class.

        """
        
        logger.info("something has been modified: %s", event.src_path)
        # `event` may be DirectoryModifiedEvent, exclude it
        if isinstance(event, FileModifiedEvent) and event.src_path == self.__target:
            logger.info("importing the raw data...")
            captured_json = None
            # to get the raw speedtest result
            with open(event.src_path, "r") as f:
                captured_json = json.load(f)
            if captured_json is None:
                raise IOError("Failed to open file" + event.src_path)
            logger.info("successfully imported the raw data")
            logger.info("make the raw data into metrics...")
            result = Parser.parse(jsondata=captured_json)
            self.__metrics.setResult(result)
            logger.info("successfully created metrics")
            logger.info("pushing metrics...")
            self.__executer.run(registry=self.__registry)
            logger.info("successfully push the metrics")
            self.__observer.unschedule_all()
            self.__observer.stop()


if __name__ == "__main__":
    logger.info("Pusher started")
    options: PusherOpitons = PusherOpitons()
    executer: Executer = Executer(options=options)
    observer = Observer()
    pusher: Pusher = Pusher(options, executer, observer)
    logger.info("Pusher has been initialized")
    observer.schedule(pusher, options.target_file_path)
    logger.info("Pusher starts to watch file...")
    observer.start()
    observer.join(timeout=options.timeout)
