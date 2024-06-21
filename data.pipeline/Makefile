# Command line overridable Environment name
Environment                     = develop

# Uppercase environment name for expansion of variable name
ENVIRONMENT_UC                  = $(shell echo $(Environment) | tr '[:lower:]' '[:upper:]')

# Reasonably stable variable names for this Makefile
EIP_STACK_NAME                      = loop-stack-elastic-ips-$(Environment)
LAMBDA_STACK_NAME                   = loop-stack-lambdas-$(Environment)
NETWORKING_STACK_NAME               = loop-stack-networking-$(Environment)
RDS_STACK_NAME                      = loop-stack-rds-$(Environment)
COGNITO_STACK_NAME                  = loop-stack-cognito-$(Environment)
STORAGE_STACK_NAME                  = loop-stack-storage-$(Environment)

# Set bucket for template upload.
TEMPLATES_BUCKET = loop-s3-cloudformation-templates-$(Environment)

# Confirmation string for destructive operations
CONFIRMATION_STRING             = "I_accept_responsibility_for_the_death_of_$(Environment)"

# Only set these for CI runs
ifneq ($(CI),)
  $(info ******** CI Run ($(Environment)) **********)
  # Use environment specific environment variables in the CI environment
  export AWS_ACCESS_KEY_ID     := $($(ENVIRONMENT_UC)_AWS_ACCESS_KEY_ID)
  export AWS_SECRET_ACCESS_KEY := $($(ENVIRONMENT_UC)_AWS_SECRET_ACCESS_KEY)
  export AWS_DEFAULT_REGION    := $($(ENVIRONMENT_UC)_AWS_DEFAULT_REGION)
  export ARTEFACTS_BUCKET      := loop-s3-artefacts-$(Environment)
else
  ifneq ($(Environment),)
    export ARTEFACTS_BUCKET      := loop-s3-artefacts-$(Environment)
  else
    export ARTEFACTS_BUCKET      := loop-s3-artefacts-develop
  endif
endif

validate-elastic-ips:
	@sam validate -t infrastructure/elastic_ips.yaml

# Elastic IPs are shared once created and export names are deterministic.
# Once this has been run once for an Environment, it should never be run
# again.
deploy-elastic-ips: validate-elastic-ips
	@echo "!! DANGER !! Enter $(CONFIRMATION_STRING) to continue..."
	@read c && test "$${c}" = $(CONFIRMATION_STRING) || exit 1
	@sam deploy \
		--capabilities CAPABILITY_IAM \
		--no-fail-on-empty-changeset \
		--parameter-overrides \
				Environment=$(Environment) \
		--stack-name $(EIP_STACK_NAME) \
		--template-file infrastructure/elastic_ips.yaml

validate-networking:
	@sam validate -t infrastructure/networking.yaml

deploy-networking: validate-networking
	@sam deploy \
		--capabilities CAPABILITY_IAM \
		--no-fail-on-empty-changeset \
		--parameter-overrides \
				Environment=$(Environment) \
		--stack-name $(NETWORKING_STACK_NAME) \
		--template-file infrastructure/networking.yaml

validate-rds:
	@sam validate -t infrastructure/rds.yaml

deploy-rds: validate-rds
	@sam deploy \
		--capabilities CAPABILITY_IAM \
		--no-fail-on-empty-changeset \
		--parameter-overrides \
				Environment=$(Environment) \
				DBMasterPassword=$(DBMasterPassword) \
				VPC=loop-export-vpc-$(Environment) \
		--stack-name $(RDS_STACK_NAME) \
		--template-file infrastructure/rds.yaml

validate-cognito:
	@sam validate -t infrastructure/cognito.yaml

deploy-cognito: validate-cognito
	@sam deploy \
		--capabilities CAPABILITY_IAM \
		--no-fail-on-empty-changeset \
		--parameter-overrides \
				Environment=$(Environment) \
		--stack-name $(COGNITO_STACK_NAME) \
		--template-file infrastructure/cognito.yaml

validate:
	@sam validate

build: template.yaml
	# Docker... if using containerised build.
	# service docker start
	# sleep 30
	# service docker status

	@ls -d $(PWD)/lambdas/* | xargs -n 1 cp -v $(PWD)/../api.common/dist/loop-1.0.tar.gz
	@cp $(PWD)/../api.common/dist/loop-1.0.tar.gz $(PWD)/loop-1.0.tar.gz
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

validate-storage:
	@sam validate -t infrastructure/storage.yaml

deploy-storage: validate-storage
	@sam deploy \
		--capabilities CAPABILITY_IAM \
		--no-fail-on-empty-changeset \
		--parameter-overrides \
				Environment=$(Environment) \
		--stack-name $(STORAGE_STACK_NAME) \
		--template-file infrastructure/storage.yaml

clean:
	rm -rf .aws-sam
