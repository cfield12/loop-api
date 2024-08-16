# Directories.
LOOP_SRC = loop-api
LOOP_GOOGLE_SRC = loop-google-api
LOOP_DEPS = $(abspath $(LOOP_SRC)/vendor)
LOOP_GOOGLE_DEPS = $(abspath $(LOOP_GOOGLE_SRC)/vendor)
CHALICE = chalice
VERSION = 1.0

# Requirements.
REQUIREMENTS = requirements.txt
PYTHON = python3
PIP = pip3
STAGE = develop
PYTEST = pytest
MIN_COVER = 80

LOOP_GOOGLE_FUNCTION_NAME = loop-google-api-$(STAGE)

# cd into api.rest
deps: .deps
.deps: $(REQUIREMENTS)
	@mkdir -p $(LOOP_DEPS)
	touch $(LOOP_DEPS)/__init__.py
	$(PIP) install --upgrade -r $(REQUIREMENTS) -t $(LOOP_DEPS)
	@touch .deps

build: .deps
	@-rm -r ../build/$(VERSION)
	@mkdir -p ../build/$(VERSION)
	cd $(LOOP_SRC) && NO_DB=1 $(CHALICE) package --stage $(STAGE) ../build/$(VERSION)

clean:
	@echo "Cleaning all artifacts..."
	-rm -rf _build $(LOOP_DEPS) .cache deps build .deps .tools $(LOOP_SRC)/vendor $(LOOP_SRC)/swagger.json swagger.json $(LOOP_SRC)/*.tmp swagger-codegen-cli.jar *.pdf
	-find . -name "*.pyc" -delete

deploy: build
	cd $(LOOP_SRC);\
	NO_DB=1 $(CHALICE) deploy --stage $(STAGE) --no-autogen-policy
	STAGE=$(STAGE) python fix_network.py

# Loop Google API
google-deps: .google-deps
.google-deps: $(REQUIREMENTS)
	@mkdir -p $(LOOP_GOOGLE_DEPS)
	touch $(LOOP_GOOGLE_DEPS)/__init__.py
	$(PIP) install --upgrade -r $(REQUIREMENTS) -t $(LOOP_GOOGLE_DEPS)
	@touch .deps

google-build: .google-deps
	@-rm -r ../build/$(VERSION)
	@mkdir -p ../build/$(VERSION)
	cd $(LOOP_GOOGLE_SRC) $(CHALICE) package --stage $(STAGE) ../build/$(VERSION)

google-clean:
	@echo "Cleaning all artifacts..."
	-rm -rf _build $(LOOP_GOOGLE_DEPS) .cache deps build .deps .tools $(LOOP_GOOGLE_SRC)/vendor $(LOOP_GOOGLE_SRC)/swagger.json swagger.json $(LOOP_GOOGLE_SRC)/*.tmp swagger-codegen-cli.jar *.pdf
	-find . -name "*.pyc" -delete

google-deploy: google-build
	cd $(LOOP_GOOGLE_SRC);\
	$(CHALICE) deploy --stage $(STAGE) --no-autogen-policy
	STAGE=$(STAGE) FUNCTION_NAME=$(LOOP_GOOGLE_FUNCTION_NAME) python fix_network.py

test:
	$(PYTHON) -m $(PYTEST) tests/ --cov=loop-api/ --cov-fail-under=$(MIN_COVER)