#!/usr/bin/env python
from setuptools import find_packages, setup

REPO_URL = (
    'https://gitlab.com/charlie.field98/back-end/-/tree/master/api.common'
)

setup(
    name='loop',
    version="1.0",
    url=REPO_URL,
    packages=find_packages(),
    package_data={
        'loop': ['data'],
    },
    install_requires=[
        'pony',
        'marshmallow',
        'python-dateutil',
        'cachetools',
        'requests',
        'boto3',
    ],
)
