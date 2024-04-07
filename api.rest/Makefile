# Directories.
SRC = loop-api
DEPS = $(abspath $(SRC)/vendor)
CHALICE = chalice
VERSION = 1.0

# Requirements.
REQUIREMENTS = requirements.txt
PYTHON = python3
PIP = pip3
STAGE = develop

# cd into api.rest
deps: .deps
.deps: $(REQUIREMENTS)
	@mkdir -p $(DEPS)
	touch $(DEPS)/__init__.py
	$(PIP) install --upgrade -r $(REQUIREMENTS) -t $(DEPS)
	@touch .deps

build: .deps
	@-rm -r ../build/$(VERSION)
	@mkdir -p ../build/$(VERSION)
	cd $(SRC) && NO_DB=1 $(CHALICE) package --stage $(STAGE) ../build/$(VERSION)

clean:
	@echo "Cleaning all artifacts..."
	-rm -rf _build $(DEPS) .cache deps build .deps .tools $(SRC)/vendor $(SRC)/swagger.json swagger.json $(SRC)/*.tmp swagger-codegen-cli.jar *.pdf
	-find . -name "*.pyc" -delete

deploy: build
	cd $(SRC);\
	NO_DB=1 $(CHALICE) deploy --stage $(STAGE) --no-autogen-policy
