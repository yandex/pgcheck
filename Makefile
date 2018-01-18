.PHONY: clean all

all: docker check

docker-clean:
	docker-compose down

docker-build:
	docker build --rm --no-cache -t pgcheck-postgres docker/pgcheck-postgres/
	docker build --rm --no-cache -t pgcheck-plproxy docker/pgcheck-plproxy/

docker-env:
	docker-compose up -d

check:
	behave --show-timings --stop @tests/pgcheck.featureset

docker: docker-clean docker-build docker-env

clean:
	rm -rf ../pgcheck_*.build ../pgcheck_*.changes ../pgcheck_*.deb

install:
	python setup.py install --root=$(DESTDIR) -O1
