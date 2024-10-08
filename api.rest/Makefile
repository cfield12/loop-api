# Directories.
LOOP_SRC = loop-api
LOOP_AUTH_SRC = auth-api
LOOP_DEPS = $(abspath $(LOOP_SRC)/vendor)
LOOP_AUTH_DEPS = $(abspath $(LOOP_AUTH_SRC)/vendor)
CHALICE = chalice
VERSION = 1.0

AUTH_FUNCTION_NAME = loop-auth-api-$(STAGE)

# Requirements.
REQUIREMENTS = requirements.txt
PYTHON = python3
PIP = pip3
STAGE = develop
PYTEST = pytest
MIN_COVER = 80

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

# Make commands for auth api
deps-auth: .deps-auth
.deps-auth: $(REQUIREMENTS)
	@mkdir -p $(LOOP_AUTH_DEPS)
	touch $(LOOP_AUTH_DEPS)/__init__.py
	$(PIP) install --upgrade -r $(REQUIREMENTS) -t $(LOOP_AUTH_DEPS)
	@touch .deps

build-auth: .deps-auth
	@-rm -r ../build/$(VERSION)
	@mkdir -p ../build/$(VERSION)
	cd $(LOOP_AUTH_SRC) && $(CHALICE) package --stage $(STAGE) ../build/$(VERSION)

clean-auth:
	@echo "Cleaning all artifacts..."
	-rm -rf _build $(LOOP_AUTH_DEPS) .cache deps build .deps .tools $(LOOP_AUTH_SRC)/vendor $(LOOP_AUTH_SRC)/swagger.json swagger.json $(LOOP_AUTH_SRC)/*.tmp swagger-codegen-cli.jar *.pdf
	-find . -name "*.pyc" -delete

deploy-auth: build
	cd $(LOOP_AUTH_SRC);\
	$(CHALICE) deploy --stage $(STAGE) --no-autogen-policy
	STAGE=$(STAGE) FUNCTION_NAME=$(AUTH_FUNCTION_NAME) python fix_network.py

test:
	$(PYTHON) -m $(PYTEST) tests/ --cov=loop-api/ --cov-fail-under=$(MIN_COVER)