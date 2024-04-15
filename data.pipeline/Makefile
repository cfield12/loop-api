# Command line overridable Environment name
Environment                     = develop

# Uppercase environment name for expansion of variable name
ENVIRONMENT_UC                  = $(shell echo $(Environment) | tr '[:lower:]' '[:upper:]')

# Reasonably stable variable names for this Makefile
LAMBDA_STACK_NAME                   = qi-stack-lambdas-$(Environment)

# Set bucket for template upload.
TEMPLATES_BUCKET = loop-s3-cloudformation-templates-$(Environment)

# Only set these for CI runs
ifneq ($(CI),)
  $(info ******** CI Run ($(Environment)) **********)
  # Use environment specific environment variables in the CI environment
  export AWS_ACCESS_KEY_ID     := $($(ENVIRONMENT_UC)_AWS_ACCESS_KEY_ID)
  export AWS_SECRET_ACCESS_KEY := $($(ENVIRONMENT_UC)_AWS_SECRET_ACCESS_KEY)
  export AWS_DEFAULT_REGION    := $($(ENVIRONMENT_UC)_AWS_DEFAULT_REGION)
  export ARTEFACTS_BUCKET      := qi-s3-artefacts-$(Environment)
else
  ifneq ($(Environment),)
    export ARTEFACTS_BUCKET      := qi-s3-artefacts-$(Environment)
  else
    export ARTEFACTS_BUCKET      := qi-s3-artefacts-develop
  endif
endif

validate:
	@sam validate

build: template.yaml
	# Docker... if using containerised build.
	# service docker start
	# sleep 30
	# service docker status

	@ls -d $(PWD)/lambdas/* | xargs -n 1 cp -v $(PWD)/../api.common/dist/loop-1.0.0.tar.gz
	@cp $(PWD)/../api.common/dist/loop-1.0.0.tar.gz $(PWD)/loop-1.0.0.tar.gz
	@sam build -t template.yaml
	@sam package --s3-bucket=$(ARTEFACTS_BUCKET) \
		--output-template-file packaged.yaml

deploy: validate build
	@sam deploy \
		--capabilities CAPABILITY_IAM \
		--no-fail-on-empty-changeset \
		--parameter-overrides \
				Environment=$(Environment) \
		--stack-name $(LAMBDA_STACK_NAME) \
		--s3-bucket $(TEMPLATES_BUCKET) \
		--template-file packaged.yaml

clean:
	rm -rf .aws-sam
