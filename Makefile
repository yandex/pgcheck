rpm:
	find . -name "*.pyc" -exec rm -rf {} \;
	find . -name "*.pyo" -exec rm -rf {} \;
	rm -rf noarch
	rpmbuild -bb pgcheck.spec
