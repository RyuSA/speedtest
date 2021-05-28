speedtest-pusher
===

speedtest-pusher is a helper tool for speedtest-cli to share the speedtest result using Prometheus Pushgateway(https://github.com/prometheus/pushgateway).

## Usage

```bash
❯ docker run --rm -it -v /path/to/speedtest.json:/var/log/speedtest.json -e TARGET_FILE_PATH="/var/log/speedtest.json" -e PUSHGATEWAY_HOST="127.0.0.1:9091" ryusa/speedtest-pusher:v2.1.3
```

## Environment Variables

- `TARGET_FILE_PATH`: path to `speedtest.json`. speedtest-pusher watches the file and push the result when speedtest-pusher detectes it's modified event.
- `PUSHGATEWAY_HOST`: the hostname of pushgateway
- `MAX_TIMEOUT`: timeout second. default: `"60"`
- `JOB_NAME`: the job name using which speedtest-pusher pushing the data to pushgateway. default: `speedtest`
