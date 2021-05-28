FROM python:3.7.10-slim-buster as builder
WORKDIR /app
COPY ./requrements.txt /app/requrements.txt
RUN pip install --no-cache-dir -r requrements.txt

FROM python:3.7.10-slim-buster
WORKDIR /app
COPY --from=builder /usr/local/lib/python3.7/ /usr/local/lib/python3.7/
COPY ./pusher.py ./pusher.py
CMD ["python", "pusher.py"]
