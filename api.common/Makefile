# Requirements.
PYTHON = python3
PYTEST = pytest
MIN_COVER = 80

test:
	$(PYTHON) -m $(PYTEST) --cov-config=.coveragerc --cov=loop --cov-fail-under=$(MIN_COVER)
