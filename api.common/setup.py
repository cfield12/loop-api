#!/usr/bin/env python
from setuptools import setup, find_packages

setup(
    name='loop',
    version="1.0",
    packages=find_packages(),
    package_data={
        'loop': ['data'],
    },
)
