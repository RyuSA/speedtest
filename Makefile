SPEEDTEST_VERSION=v2.1.3

build: 
	docker build -t ryusa/speedtest:${SPEEDTEST_VERSION} . --build-arg SPEEDTEST_VERSION=${SPEEDTEST_VERSION}

build-pusher:
	docker build -t ryusa/speedtest-pusher:${SPEEDTEST_VERSION} ./pusher/

push: build
	docker push ryusa/speedtest:${SPEEDTEST_VERSION}

push-pusher: build-pusher
	docker push ryusa/speedtest-pusher:${SPEEDTEST_VERSION}
