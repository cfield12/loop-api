#!/usr/bin/env python
from setuptools import setup, find_packages
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
)
