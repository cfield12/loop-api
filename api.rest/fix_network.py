import os
from pprint import pprint

import boto3

STAGE = os.environ['STAGE']
FUNCTION_NAME = os.environ.get('FUNCTION_NAME', f'loop-api-{STAGE}')

VARIABLES = {
    'PROJECT': 'loop',
    'ENVIRONMENT': STAGE,
}


class FunctionConfigurator:
    def __init__(self):
        print('Updating lambda network configuration.')
        session = boto3.session.Session()
        self.lambda_client = session.client('lambda')
        cfn_client = session.client('cloudformation')
        exports = cfn_client.list_exports()
        self.exports = exports['Exports']
        next_token = exports.get('NextToken', None)
        while next_token:
            exports = cfn_client.list_exports(NextToken=next_token)
            self.exports += exports['Exports']
            next_token = exports.get('NextToken', None)

        self.functions = dict()
        self.first_marker = True

        self.all_lambdas = dict()
        self.function_to_patch = dict()

    def _get_functions(self, marker: str) -> dict:
        try:
            if marker is None:
                print('Getting the first batch...')
                functions = self.lambda_client.list_functions(MaxItems=50)
            else:
                print('Getting the next batch...')
                functions = self.lambda_client.list_functions(
                    MaxItems=50, Marker=marker
                )
            return functions
        except Exception as e:
            print(e)

    def _process_functions(self, functions: dict):
        function_names = functions['Functions']
        named_lambda = {
            function['FunctionName']: function for function in function_names
        }
        self.all_lambdas.update(named_lambda)

    def set_function_to_patch(self):
        marker = None
        functions = self._get_functions(marker)
        self._process_functions(functions)
        marker = functions.get('NextMarker')
        while marker:
            functions = self._get_functions(marker)
            self._process_functions(functions)
            marker = functions.get('NextMarker')

        self.function_to_patch = self.all_lambdas.get(FUNCTION_NAME)

    def update_function(self):
        loop_subnets = [
            export['Value'].split(',')
            for export in self.exports
            if export['Name'] == f'loop-export-subnet-list-private-{STAGE}'
        ][0]
        pprint(loop_subnets)

        loop_security_groups = [
            export['Value'].split(',')
            for export in self.exports
            if export['Name']
            == f'loop-export-security-group-list-private-{STAGE}'
        ][0]
        pprint(loop_security_groups)

        function_name = self.function_to_patch['FunctionName']
        print(
            f'Going to patch configuration to {function_name} '
            'in order to allow it access to RDS...'
        )
        configuration = {
            'FunctionName': function_name,
            'VpcConfig': {
                'SubnetIds': loop_subnets,
                'SecurityGroupIds': loop_security_groups,
            },
            'Environment': {'Variables': VARIABLES},
        }

        print('\nConfiguration:')
        pprint(configuration)

        print('\nOutput:')
        pprint(
            self.lambda_client.update_function_configuration(**configuration)
        )


if __name__ == '__main__':
    configurator = FunctionConfigurator()
    configurator.set_function_to_patch()
    configurator.update_function()
