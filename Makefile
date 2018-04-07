.PHONY: clean all

all: docker check

build:
	GOOS=linux GOARCH=amd64 go build -o pgcheck

docker-build:
	docker build --rm --no-cache -t pgcheck-postgres docker/pgcheck-postgres/
	docker build --rm --no-cache -t pgcheck-plproxy docker/pgcheck-plproxy/

docker-env:
	docker-compose down
	docker-compose up -d

check:
	behave --show-timings --stop --tags=-long @tests/pgcheck.featureset

check-world:
	behave --show-timings --stop @tests/pgcheck.featureset

docker: build docker-build docker-env
