.PHONY: clean all

clean:
	rm -rf ../pgcheck_*.build ../pgcheck_*.changes ../pgcheck_*.deb

install:
	python setup.py install --root=$(DESTDIR) -O1
