import logging
import os


def set_up_root_logger(dd_host='intake.logs.datadoghq.com',
                       dd_port=10516,
                       dd_key=None,
                       dd_service=None,
                       dd_app_host=None,
                       dd_extra=None,
                       level=logging.DEBUG,
                       logger_name=None):
    global _dd_key
    global _logger

    # Attempt to use standard environment variable if available
    if not dd_key:
        dd_key = _dd_key

    # If this is a lambda environment, set up extra meta data for logger
    if 'AWS_LAMBDA_FUNCTION_NAME' in os.environ:
        aws_lambda_metadata = {
            'AWS_REGION': os.environ.get('AWS_REGION'),
            'AWS_EXECUTION_ENV': os.environ.get('AWS_EXECUTION_ENV'),
            'AWS_LAMBDA_FUNCTION_NAME': os.environ.get('AWS_LAMBDA_FUNCTION_NAME'),
            'AWS_LAMBDA_FUNCTION_MEMORY_SIZE': os.environ.get('AWS_LAMBDA_FUNCTION_MEMORY_SIZE'),
            'AWS_LAMBDA_FUNCTION_VERSION': os.environ.get('AWS_LAMBDA_FUNCTION_VERSION'),
            'AWS_LAMBDA_LOG_GROUP_NAME': os.environ.get('AWS_LAMBDA_LOG_GROUP_NAME'),
            'environment': os.environ.get('ENVIRONMENT'),
            'project': os.environ.get('PROJECT')
        }
        if not dd_service:
            dd_service = aws_lambda_metadata['AWS_LAMBDA_FUNCTION_NAME']
        if not dd_app_host:
            dd_app_host = 'aws-lambda'
        if not dd_extra:
            dd_extra = aws_lambda_metadata
        else:
            # Allow provided dict to take precedence
            aws_lambda_metadata.update(dd_extra)
            dd_extra = aws_lambda_metadata
    else:
        # If this is not a lambda, apply old defaults
        if not dd_service:
            dd_service = 'qi-service'
        if not dd_app_host:
            dd_app_host = 'localhost'
        # Note that a dict is expected for datadog's `extra` field
        if not dd_extra:
            dd_extra = {}

    if not logger_name:
        logger = logging.getLogger()
        _logger = logger
    else:
        logger = logging.getLogger(logger_name)

    # Use cached logger if available
    logger.setLevel(level)

    # Only enable datadog if a key is provided
    if dd_key:
        datadog_handler = SocketHandlerDataDog(dd_host, dd_port, key=dd_key, tls=True)
        datadog_formatter = JSONFormatterDataDog(service=dd_service,
                                                 host=dd_app_host,
                                                 extra=dd_extra)
        datadog_handler.setFormatter(datadog_formatter)
        logger.addHandler(datadog_handler)

    console_handler = StreamHandlerStdoutStderr()
    if 'AWS_LAMBDA_FUNCTION_NAME' in os.environ:
        console_formatter = JSONFormatterDataDog(service=None,
                                                 host=None,
                                                 extra=dd_extra)
    else:
        console_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    return logger