.PHONY: test

test:
	python3 -m py_compile oci_retry.py oci_retry_micro.py
	python3 tests/test_configuration.py
